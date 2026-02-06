import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.trends import TrendsScraper

async def test_trends():
    print("Testing Trends Scraper...")
    scraper = TrendsScraper(headless=False)
    
    try:
        trends = await scraper.get_top_trends()
        print("\n--- TRENDS FOUND ---")
        for t in trends:
            print(f"- {t}")
            
        if not trends:
            print("No trends found. Selectors might be wrong.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_trends())
