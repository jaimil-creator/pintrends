import asyncio
import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import Keyword, TrendKeyword, Suggestion
from scraper.trends import TrendsScraper
from scraper.suggestions import SuggestionsScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperPipeline:
    def __init__(self):
        self.trends_scraper = TrendsScraper()
        self.suggestions_scraper = SuggestionsScraper()
        self.db = SessionLocal()

    async def run(
        self, 
        country: str = "US", 
        trend_type: str = "growing",
        interests: list = None,
        ages: list = None,
        genders: list = None
    ):
        try:
            # 1. Scrape Trends
            logger.info(f"Starting Trends Scraping ({country}, {trend_type})...")
            # Log filters
            if interests: logger.info(f"Interests: {interests}")
            if ages: logger.info(f"Ages: {ages}")
            if genders: logger.info(f"Genders: {genders}")
            
            trends = await self.trends_scraper.get_top_trends(
                country=country, 
                trend_type=trend_type, 
                interests=interests, 
                ages=ages, 
                genders=genders
            )
            logger.info(f"Found {len(trends)} trends.")
            
            if not trends:
                logger.warning("No trends found. Aborting pipeline.")
                return

            for trend_data in trends:
                await self.process_trend(trend_data, country, trend_type, interests, ages, genders)
                
        finally:
            self.db.close()
            # Close browsers
            if self.trends_scraper.browser.page:
                await self.trends_scraper.browser.close()
            if self.suggestions_scraper.browser.page:
                await self.suggestions_scraper.browser.close()

    async def process_trend(
        self, 
        trend_data: dict, 
        country: str, 
        trend_type: str,
        interests: list = None,
        ages: list = None,
        genders: list = None
    ):
        trend_text = trend_data["keyword"]
        logger.info(f"Processing trend: {trend_text}")
        
        # Format filters for DB (comma-separated strings)
        f_interests = ",".join(interests) if interests else None
        f_ages = ",".join(ages) if ages else None
        f_genders = ",".join(genders) if genders else None
        
        # 1.5 Fetch Prediction Data
        prediction_json = None
        try:
            # We use the sync method from scraper (it uses requests)
            # Since pipeline is async, strictly we should run in threadpool if blocking, 
            # but for MVP requests is fast enough or use sync call.
            pred_data = self.trends_scraper.get_trend_prediction(trend_text, country)
            if pred_data:
                prediction_json = json.dumps(pred_data)
        except Exception as e:
            logger.error(f"Failed to get predictions for {trend_text}: {e}")

        # 1. Save TrendKeyword (Log History)
        # Always create new record to track history
        trend_record = TrendKeyword(
            keyword=trend_text, 
            country=country,
            trend_type=trend_type,
            detected_at=datetime.utcnow(),
            filter_interests=f_interests,
            filter_ages=f_ages,
            filter_genders=f_genders,
            weekly_change=trend_data.get("weekly_change"),
            monthly_change=trend_data.get("monthly_change"),
            yearly_change=trend_data.get("yearly_change"),
            prediction_data=prediction_json
        )
        self.db.add(trend_record)
        self.db.commit() # Commit to get ID if needed, but mainly to save log
        
        # 2. Ensure Keyword exists (Main table)
        keyword_obj = self.db.query(Keyword).filter(Keyword.keyword == trend_text).first()
        if not keyword_obj:
            keyword_obj = Keyword(keyword=trend_text, last_scraped=datetime.utcnow())
            self.db.add(keyword_obj)
            self.db.commit()
            self.db.refresh(keyword_obj)
        else:
            keyword_obj.last_scraped = datetime.utcnow()
            self.db.commit()
        
        # 3. Get Suggestions (DISABLED - On Demand Only)
        # logger.info(f"Fetching suggestions for '{trend_text}'...")
        # suggestions = await self.suggestions_scraper.get_suggestions(trend_text)
        # logger.info(f"Found {len(suggestions)} suggestions.")
        
        # 4. Store Suggestions (Log History)
        # Always insert new suggestions with timestamp
        # for sugg_text in suggestions:
        #     new_sugg = Suggestion(
        #         parent_keyword_id=keyword_obj.id, 
        #         suggestion=sugg_text,
        #         detected_at=datetime.utcnow()
        #     )
        #     self.db.add(new_sugg)
        
        # self.db.commit()
        
        # Rate Limiting
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    pipeline = ScraperPipeline()
    asyncio.run(pipeline.run())
