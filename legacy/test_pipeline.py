import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.engine import PinterestScraper
from analysis.scoring import ScoreCalculator
from database.db import SessionLocal
from database.repository import KeywordRepository

async def test_pipeline():
    print("Starting Pipeline Test...")
    
    # 1. Scrape
    print("Step 1: Scraping...")
    scraper = PinterestScraper(headless=False)
    await scraper.start()
    try:
        data = await scraper.scrape_keyword("cyberpunk city")
    finally:
        await scraper.close()
        
    if not data['pins']:
        print("Scraping failed to find pins.")
        return

    print(f"Found {len(data['pins'])} pins.")

    # 2. Score
    print("Step 2: Scoring...")
    calculator = ScoreCalculator()
    metrics = calculator.calculate(data['pins'])
    bucket = calculator.get_bucket(metrics['score'])
    print(f"Score: {metrics['score']} ({bucket})")

    # 3. Save to DB
    print("Step 3: Saving to DB...")
    db = SessionLocal()
    repo = KeywordRepository(db)
    
    # Create/Get Keyword
    keyword_obj = repo.get_keyword(data['keyword'])
    if not keyword_obj:
        keyword_obj = repo.create_keyword(data['keyword'])
    
    # Add Metrics
    repo.add_metrics(
        keyword_id=keyword_obj.id,
        score=metrics['score'],
        total_pins=metrics['total_pins'],
        avg_saves=metrics['avg_saves']
    )
    
    # Add Pins
    repo.add_pins(keyword_obj.id, data['pins'])
    
    repo.update_last_scraped(keyword_obj.id, datetime.utcnow())
    
    print("Data saved successfully.")

    # 4. Verify
    print("Step 4: Reading from DB...")
    history = repo.get_history(keyword_obj.id)
    print(f"History entries: {len(history)}")
    print(f"Latest Score: {history[-1].score}")
    
    db.close()
    print("Pipeline Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
