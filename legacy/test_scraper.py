import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.engine import PinterestScraper

async def test_run():
    print("Starting Scraper Test...")
    scraper = PinterestScraper(headless=False) # Headful to see what happens
    
    try:
        await scraper.start()
        keyword = "minimalist desk setup"
        print(f"Searching for: {keyword}")
        
        data = await scraper.scrape_keyword(keyword)
        
        print("\n--- RESULTS ---")
        print(f"Keyword: {data.get('keyword')}")
        pins = data.get('pins', [])
        print(f"Total Pins found: {len(pins)}")
        
        if pins:
            print("\nTop 3 Pins:")
            for i, p in enumerate(pins[:3]):
                print(f"{i+1}. {p['title']} ({p['saves']} saves) - {p['url']}")
        else:
            print("WARNING: No pins found. Selectors might be broken.")
            
        related = data.get('related_keywords', [])
        print(f"\nRelated Keywords: {related}")
        
    except Exception as e:
        print(f"TEST FAILED: {e}")
    finally:
        print("\nClosing browser...")
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_run())
