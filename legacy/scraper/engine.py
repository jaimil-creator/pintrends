import asyncio
from typing import Dict, List, Optional
from .browser import PinterestBrowser
from .parser import PinterestParser

class PinterestScraper:
    def __init__(self, headless: bool = False):
        self.browser = PinterestBrowser(headless=headless)
        self.parser = PinterestParser()

    async def start(self):
        await self.browser.start()

    async def close(self):
        await self.browser.close()

    async def scrape_keyword(self, keyword: str) -> Dict:
        """
        Scrapes Pinterest for a given keyword using the search URL.
        """
        search_url = f"https://www.pinterest.com/search/pins/?q={keyword}&rs=typed"
        print(f"Scraping keyword: {keyword} at {search_url}")

        try:
            await self.browser.navigate(search_url)
            
            # Scroll a few times to load more pins
            await self.browser.scroll_to_bottom(times=3)
            
            # Get HTML content
            html_content = await self.browser.get_content()
            
            # Parse data
            data = self.parser.parse_search_results(html_content)
            data["keyword"] = keyword
            
            return data
            
        except Exception as e:
            print(f"Error scraping {keyword}: {e}")
            return {"keyword": keyword, "pins": [], "related_keywords": [], "error": str(e)}

if __name__ == "__main__":
    # Simple manual test
    async def main():
        scraper = PinterestScraper(headless=False)
        await scraper.start()
        try:
            result = await scraper.scrape_keyword("home office setup")
            print(f"Found {len(result['pins'])} pins")
            print(f"Related: {result['related_keywords']}")
            if result['pins']:
                print(f"Sample Pin: {result['pins'][0]}")
        finally:
            await scraper.close()

    asyncio.run(main())
