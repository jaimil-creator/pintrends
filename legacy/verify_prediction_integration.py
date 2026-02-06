from scraper.trends import TrendsScraper
from database.db import SessionLocal
from database.models import TrendKeyword
from datetime import datetime
import json
import sys

def verify_integration():
    print("Initializing Scraper...")
    scraper = TrendsScraper(headless=True)
    
    keyword = "old lady costume"
    country = "US"
    
    print(f"Fetching prediction data for '{keyword}'...")
    pred_data = scraper.get_trend_prediction(keyword, country)
    
    if not pred_data:
        print("No data fetched! Check scraper logic.")
        return
        
    print(f"Fetched {len(pred_data)} data points for prediction.")
    
    # Save to DB
    print("Saving to Database...")
    db = SessionLocal()
    
    try:
        # Check if exists
        existing = db.query(TrendKeyword).filter(
            TrendKeyword.keyword == keyword, 
            TrendKeyword.country == country
        ).first()
        
        prediction_json = json.dumps(pred_data)
        
        if existing:
            print("Updating existing record...")
            existing.prediction_data = prediction_json
            existing.detected_at = datetime.utcnow() # Update time to appear at top
        else:
            print("Creating new record...")
            new_trend = TrendKeyword(
                keyword=keyword,
                country=country,
                trend_type="growing",
                detected_at=datetime.utcnow(),
                prediction_data=prediction_json,
                weekly_change="50%", 
                monthly_change="200%",
                yearly_change="500%"
            )
            db.add(new_trend)
            
        db.commit()
        print(f"Success! Prediction data saved for '{keyword}'.")
        print("Please check the UI Trends Explorer -> Deep Dive for this keyword.")
        
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_integration()
