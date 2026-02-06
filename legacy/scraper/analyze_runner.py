import sys
import asyncio
import os
import argparse
from datetime import datetime

# Adjust path to find modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from database import repository
from scraper.engine import PinterestScraper
from analysis.scoring import ScoreCalculator

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def analyze_keyword_task(keyword: str):
    print(f"Starting analysis for: {keyword}")
    db = SessionLocal()
    
    try:
        scraper = PinterestScraper(headless=True) # Headless=True for background
        await scraper.start()
        
        print(f"Scraping '{keyword}'...")
        data = await scraper.scrape_keyword(keyword)
        await scraper.close()
        
        pins = data.get("pins", [])
        if not pins:
            print("No pins found.")
            return

        # Score Calculation
        calc = ScoreCalculator()
        metrics = calc.calculate(pins)
        
        repo = repository.KeywordRepository(db)
        
        # Upsert keyword
        kw = repo.get_keyword(keyword)
        if not kw:
            kw = repo.create_keyword(keyword)
            
        repo.add_metrics(kw.id, metrics['score'], metrics['total_pins'], metrics['avg_saves'])
        
        # Save Pins (Limit to top if needed, but saving all is better for history)
        # User requested top 15, we'll save them all but UI shows 50.
        repo.add_pins(kw.id, pins)
        repo.update_last_scraped(kw.id, datetime.utcnow())
        
        print(f"Analysis completed for {keyword}. Found {len(pins)} pins. Score: {metrics['score']}")
        
    except Exception as e:
        print(f"Analysis failed for {keyword}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", help="Keyword to analyze")
    args = parser.parse_args()
    
    asyncio.run(analyze_keyword_task(args.keyword))
