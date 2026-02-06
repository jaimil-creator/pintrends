import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.suggestions import SuggestionsScraper

async def test_suggestions():
    print("Testing Suggestions Scraper...")
    scraper = SuggestionsScraper(headless=False)
    
    try:
        # Test with a known broad keyword
        keyword = "home decor"
        suggestions = await scraper.get_suggestions(keyword)
        
        print(f"\nSuggestions for '{keyword}':")
        for s in suggestions:
            print(f"- {s}")
            
        if not suggestions:
            print("No suggestions found.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_suggestions())
