import asyncio
from scraper.trends import TrendsScraper
import json

def test_fetch():
    scraper = TrendsScraper()
    # Test with a known trend
    keyword = "valentines nails"
    country = "US"
    
    print(f"Testing fetch for '{keyword}'...")
    data = scraper.get_trend_prediction(keyword, country)
    
    if data:
        print("Success! Data received.")
        print(json.dumps(data[:3], indent=2)) # Print first 3 points
    else:
        print("No data received.")

if __name__ == "__main__":
    test_fetch()
