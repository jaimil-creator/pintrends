from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import asyncio
import sys

# Windows-specific event loop policy to allow subprocesses (required by Playwright)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from database.db import get_db
from database import repository, models
from . import schemas
from scraper.engine import PinterestScraper
from analysis.scoring import ScoreCalculator
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeywordPayload(BaseModel):
    keyword: str

app = FastAPI(title="PinTrends API")

@app.on_event("startup")
async def startup_event():
    # Helper to ensure browser resources are ready if needed, or warm up
    pass

@app.get("/")
def read_root():
    return {"message": "PinTrends API is running"}

async def scrape_job(keyword: str, db: Session):
    print(f"Starting background job for: {keyword}")
    # Note: In a real app, use a proper session handling for async jobs.
    # Here we might need a fresh session or careful handling.
    # For simplicity, we'll create a new session in the job.
    
    from database.db import SessionLocal
    job_db = SessionLocal()
    
    try:
        scraper = PinterestScraper(headless=False) # Headful required for Pinterest
        await scraper.start()
        data = await scraper.scrape_keyword(keyword)
        await scraper.close()
        
        if not data.get("pins"):
            print("No pins found in background job.")
            return

        calc = ScoreCalculator()
        metrics = calc.calculate(data["pins"])
        
        repo = repository.KeywordRepository(job_db)
        
        # Upsert keyword
        kw = repo.get_keyword(keyword)
        if not kw:
            kw = repo.create_keyword(keyword)
            
        repo.add_metrics(kw.id, metrics['score'], metrics['total_pins'], metrics['avg_saves'])
        repo.add_pins(kw.id, data['pins'])
        repo.update_last_scraped(kw.id, datetime.utcnow())
        
        print(f"Job completed for {keyword}. Score: {metrics['score']}")
        
    except Exception as e:
        print(f"Job failed for {keyword}: {e}")
    finally:
        job_db.close()


# We don't need the async job anymore, we will launch a script.
@app.post("/scrape-trends")
async def scrape_trends(
    request: schemas.ScrapeTrendsRequest,
):
    """
    Triggers a background job to scrape trends with specified country and type.
    """
    print(f"Launching external pipeline for {request.country}, {request.trend_type}")
    
    # Run the pipeline script as a separate process
    # We pass args via env vars or command line arguments.
    # Let's create a dedicated runner script or just pass args to run_pipeline.py if updated.
    
    # For now, let's just use run_pipeline.py? 
    # run_pipeline.py currently has no args support.
    # We should update run_pipeline.py or create a new entry point.
    
    # Let's interact with the python script:
    cmd = [
        sys.executable, 
        "scraper/pipeline_runner.py", 
        "--country", request.country, 
        "--type", request.trend_type
    ]
    
    if request.interests:
        cmd.extend(["--interests", ",".join(request.interests)])
    if request.ages:
        cmd.extend(["--ages", ",".join(request.ages)])
    if request.genders:
        cmd.extend(["--genders", ",".join(request.genders)])
    
    import subprocess
    # Run detached/background
    subprocess.Popen(cmd)
    
    return {"message": f"Trend scraping process launched for {request.country}/{request.trend_type}"}

@app.post("/analyze-keyword", response_model=dict)
async def analyze_keyword(
    request: schemas.AnalyzeRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Triggers a background scrape job. Returns immediately.
    """
    keyword = request.keyword
    
    # Check cache logic
    repo = repository.KeywordRepository(db)
    kw = repo.get_keyword(keyword)
    
    if kw and kw.last_scraped and not request.force_rescrape:
        # Check if scraped recently (e.g. today)
        # For simplicity, just return message saying cached data is available
        return {"message": "Data already cached. Fetch details via GET.", "cached": True}

    # background_tasks.add_task(scrape_job, keyword, db)
    # Use subprocess to avoid Windows Event Loop issues with Playwright+Uvicorn
    cmd = [
        sys.executable,
        "scraper/analyze_runner.py",
        keyword
    ]
    import subprocess
    # Redirect output to file for debugging
    with open("analysis_debug.log", "a") as outfile:
        subprocess.Popen(cmd, stdout=outfile, stderr=outfile)
    
    return {"message": f"Analysis started for '{keyword}'. Check results in a few seconds.", "cached": False}

@app.get("/keyword/{keyword}", response_model=schemas.KeywordResponse)
def get_keyword_details(keyword: str, db: Session = Depends(get_db)):
    repo = repository.KeywordRepository(db)
    kw = repo.get_keyword(keyword)
    
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found or not yet analyzed.")
    
    history = repo.get_history(kw.id)
    latest_metrics = history[-1] if history else None
    
    # Get latest pins
    pins_query = db.query(models.Pin).filter(models.Pin.keyword_id == kw.id).limit(50).all()
    
    calc = ScoreCalculator()
    current_score = latest_metrics.score if latest_metrics else 0.0
    bucket = calc.get_bucket(current_score)
    
    return {
        "keyword": kw.keyword,
        "last_scraped": kw.last_scraped,
        "current_score": current_score,
        "bucket": bucket,
        "pins": [
            {"title": p.title, "url": p.pin_url, "saves": p.saves}
            for p in pins_query
        ],
        "history": history
    }

@app.get("/trends", response_model=List[schemas.KeywordResponse])
def get_trends(keywords: str, db: Session = Depends(get_db)):
    # keywords comma separated
    kw_list = keywords.split(",")
    results = []
    for k in kw_list:
        try:
            res = get_keyword_details(k.strip(), db)
            results.append(res)
        except HTTPException:
            continue
@app.post("/generate-combinations", response_model=List[str])
def generate_combinations(request: schemas.GenerateCombinationsRequest):
    """
    Generates SEO keyword combinations using OpenRouter's free model.
    """
    import requests
    import json
    
    # Construct the prompt
    sugg_str = ", ".join(request.suggestions)
    prompt = (
        f"I have a base keyword: '{request.keyword}' and a list of suggestion words: {sugg_str}. "
        f"Please combine the base keyword with these suggestion words to create natural, "
        f"SEO-friendly long-tail keywords that people typically search for on Pinterest. "
        f"Return ONLY a valid JSON array of strings (e.g., [\"keyword 1\", \"keyword 2\"]). "
        f"Do not include any other text."
    )
    
    try:
        response = requests.post(
          url="https://openrouter.ai/api/v1/chat/completions",
          headers={
            "Authorization": f"Bearer {request.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000", # Required by OpenRouter for free tier
            "X-Title": "PinTrends Local",
          },
          data=json.dumps({
            "model": "openrouter/free", # Using a reliable free model
            "messages": [
                {
                  "role": "user",
                  "content": prompt
                }
              ]
          })
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"OpenRouter Error: {response.text}")
            
        json_resp = response.json()
        content = json_resp['choices'][0]['message']['content']
        
        # Clean up code blocks if model returns them
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON
        try:
            keywords = json.loads(content)
            if isinstance(keywords, list):
                return keywords
            else:
                 # Fallback if not list
                 return [str(keywords)]
        except json.JSONDecodeError:
            # Fallback text parsing if JSON fails
            lines = content.split("\n")
            return [l.strip("- ").strip() for l in lines if l.strip()]
            
    except Exception as e:
        print(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- New Endpoint: Scrape Suggestions On Demand ---
@app.post("/scrape-suggestions")
def scrape_suggestions_endpoint(payload: KeywordPayload, db: Session = Depends(get_db)):
    """
    On-demand scrape for suggestions.
    """
    keyword_text = payload.keyword
    logger.info(f"On-demand suggestion scrape for: {keyword_text}")
    
    # Check if we recently scraped (optional, but good practice)
    # For now, we assume user wants fresh data if they clicked the button
    
    from scraper.suggestions import SuggestionsScraper
    import asyncio
    
    try:
        scraper = SuggestionsScraper()
        
        async def run_scrape():
            await scraper.browser.start()
            try:
                results = await scraper.get_suggestions(keyword_text)
                return results
            finally:
                await scraper.browser.close()
        
        # Run async scraper
        suggestions = asyncio.run(run_scrape())
        
        if not suggestions:
            return {"status": "success", "suggestions": [], "message": "No suggestions found."}
            
        # Save to DB
        # Find parent keyword id
        from database.models import Keyword, Suggestion
        kw_obj = db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
        if not kw_obj:
            # Should technically exist if we are analyzing it, but safety check
            kw_obj = Keyword(keyword=keyword_text, last_scraped=datetime.utcnow())
            db.add(kw_obj)
            db.commit()
            db.refresh(kw_obj)
            
        # Add new suggestions
        count = 0
        for s_text in suggestions:
            # Optional: Check dupes if needed, or just append log style
            # For simplicity, we just add them. (Cleanup script handles dupes later if needed)
            s = Suggestion(parent_keyword_id=kw_obj.id, suggestion=s_text, detected_at=datetime.utcnow())
            db.add(s)
            count += 1
            
        db.commit()
        return {"status": "success", "count": count, "suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Suggestion scrape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
