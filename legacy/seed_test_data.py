from database.db import SessionLocal
from database.models import TrendKeyword
from datetime import datetime

def seed_data():
    db = SessionLocal()
    keyword = "old lady costume"
    
    # Check if exists
    exists = db.query(TrendKeyword).filter(TrendKeyword.keyword == keyword).first()
    
    if not exists:
        print(f"Seeding '{keyword}'...")
        # Create dummy entry - exact fields needed for UI to list it
        trend = TrendKeyword(
            keyword=keyword,
            detected_at=datetime.utcnow(),
            country="US",
            trend_type="growing",
            weekly_change="10%",
            monthly_change="50%",
            yearly_change="100%",
            prediction_data=None # Will trigger the 'Fetch' button logic
        )
        db.add(trend)
        db.commit()
        print("Seeded successfully.")
    else:
        print(f"'{keyword}' already exists.")
        # Ensure country is US for test consistency
        if exists.country != "US":
            exists.country = "US"
            db.commit()
            print("Updated country to US.")

    db.close()

if __name__ == "__main__":
    seed_data()
