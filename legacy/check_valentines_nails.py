from database.db import SessionLocal
from database.models import Keyword, Pin
from datetime import datetime

def check_data():
    db = SessionLocal()
    keyword = "valentines nails"
    kw = db.query(Keyword).filter(Keyword.keyword == keyword).first()
    
    if kw:
        print(f"Keyword: {kw.keyword}, Last Scraped: {kw.last_scraped}")
        pins = db.query(Pin).filter(Pin.keyword_id == kw.id).all()
        print(f"Total Pins in DB: {len(pins)}")
        
        # Check specific pin data
        if pins:
            print(f"First Pin: {pins[0].title} | Saves: {pins[0].saves}")
    else:
        print("Keyword not found.")
    db.close()

if __name__ == "__main__":
    check_data()
