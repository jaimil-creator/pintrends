from sqlalchemy.orm import Session
from datetime import date
from . import models

class KeywordRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_keyword(self, keyword_str: str):
        return self.db.query(models.Keyword).filter(models.Keyword.keyword == keyword_str).first()

    def create_keyword(self, keyword_str: str):
        db_keyword = models.Keyword(keyword=keyword_str, last_scraped=None)
        self.db.add(db_keyword)
        self.db.commit()
        self.db.refresh(db_keyword)
        return db_keyword

    def update_last_scraped(self, keyword_id: int, scraped_at):
        keyword = self.db.query(models.Keyword).filter(models.Keyword.id == keyword_id).first()
        if keyword:
            keyword.last_scraped = scraped_at
            self.db.commit()

    def add_metrics(self, keyword_id: int, score: float, total_pins: int, avg_saves: float):
        metrics = models.KeywordMetrics(
            keyword_id=keyword_id,
            date=date.today(),
            score=score,
            total_pins=total_pins,
            avg_saves=avg_saves
        )
        self.db.add(metrics)
        self.db.commit()
        return metrics

    def add_pins(self, keyword_id: int, pins_data: list):
        # Optional: delete old pins for this keyword to keep data fresh/manageable
        # self.db.query(models.Pin).filter(models.Pin.keyword_id == keyword_id).delete()
        
        for p in pins_data:
            pin = models.Pin(
                keyword_id=keyword_id,
                pin_url=p.get("url"),
                title=p.get("title"),
                saves=p.get("saves", 0)
            )
            self.db.add(pin)
        self.db.commit()

    def get_history(self, keyword_id: int):
         return self.db.query(models.KeywordMetrics)\
            .filter(models.KeywordMetrics.keyword_id == keyword_id)\
            .order_by(models.KeywordMetrics.date.asc())\
            .all()
