from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class PinSchema(BaseModel):
    title: str
    url: str
    saves: int

class KeywordMetricsSchema(BaseModel):
    date: date
    score: float
    total_pins: int
    avg_saves: float
    
    class Config:
        from_attributes = True

class KeywordResponse(BaseModel):
    keyword: str
    last_scraped: Optional[datetime]
    current_score: float
    bucket: str
    pins: List[PinSchema]
    history: List[KeywordMetricsSchema]

class AnalyzeRequest(BaseModel):
    keyword: str
    force_rescrape: bool = False

class ScrapeTrendsRequest(BaseModel):
    country: str = "US" 
    trend_type: str = "growing"
    interests: Optional[List[str]] = None
    ages: Optional[List[str]] = None
    genders: Optional[List[str]] = None

class GenerateCombinationsRequest(BaseModel):
    keyword: str
    suggestions: List[str]
    api_key: str
