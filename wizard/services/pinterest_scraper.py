import asyncio
from typing import List
from bs4 import BeautifulSoup
import requests
import re
from .browser import PinterestBrowser

class PinterestScraperService:
    def __init__(self, headless: bool = False):
        self.headless = headless

    async def get_top_trends(self, country="US", trend_type="3", interests="", age="", gender="") -> List[dict]:
        """Scrapes trending keywords from Pinterest Trends.
        
        Args:
            country: ISO 3166-2 country code (e.g., 'US', 'CA', 'DE+AT+CH')
            trend_type: trendsPreset value (1=monthly, 2=yearly, 3=growing, 4=seasonal)
            interests: Interest IDs joined by %7C (e.g., '918105274631%7C961238559656')
            age: Age bucket (e.g., '18-24', '25-34')
            gender: Gender filter ('female', 'male', 'unspecified')
        """
        browser = PinterestBrowser(headless=self.headless)
        try:
            await browser.start()
            
            # Handle both preset numbers and legacy string names
            preset_map = {"growing": "3", "seasonal": "4", "monthly": "1", "yearly": "2"}
            if trend_type in preset_map:
                preset = preset_map[trend_type]
            else:
                preset = trend_type  # Already a number
            
            # Build URL with base params
            url = f"https://trends.pinterest.com/search/?country={country}&trendsPreset={preset}"
            
            # Add optional filters
            if interests:
                url += f"&l1InterestIds={interests}"
            if age:
                url += f"&ageBucket={age}"
            if gender:
                url += f"&gender={gender}"
            
            print(f"Scraping trends from: {url}")
            await browser.navigate(url)
            await asyncio.sleep(8) # Wait for table load
            
            html = await browser.get_content()
            soup = BeautifulSoup(html, "html.parser")
            
            trends = []
            rows = soup.find_all("tr")
            for row in rows:
                try:
                    # Find keyword
                    keyword_div = row.find("div", {"data-test-id": "trends-table-term"})
                    if not keyword_div: continue
                        
                    keyword = keyword_div.get_text(strip=True)
                    if not keyword: continue
                    
                    trends.append({"keyword": keyword})
                except:
                    continue
            
            # Deduplicate
            unique = []
            seen = set()
            for t in trends:
                if t['keyword'] not in seen:
                    unique.append(t)
                    seen.add(t['keyword'])
            
            return unique
            
        finally:
            await browser.close()

    async def get_suggestions(self, keyword: str) -> List[str]:
        """Scrapes suggestions for a specific keyword."""
        browser = PinterestBrowser(headless=self.headless)
        try:
            await browser.start()
            url = f"https://www.pinterest.com/search/pins/?q={keyword}&rs=typed"
            print(f"Scraping suggestions for: {keyword}")
            
            await browser.navigate(url)
            await asyncio.sleep(4)
            
            if not browser.page: return []
            
            suggestions = []
            
            # Selector logic (from legacy suggestions.py)
            results = browser.page.locator('.KvKvqR > div > div')
            count = await results.count()
            
            if count == 0:
                 # Fallback
                 results = browser.page.locator('[data-test-id="guided-search-guide"]')
                 count = await results.count()
            
            for i in range(count):
                text = await results.nth(i).text_content()
                if text:
                    raw = text.strip()
                    # CamelCase split trick
                    formatted = re.sub(r'(?<=[a-z])(?=[A-Z])', ', ', raw)
                    suggestions.append(formatted)
            
            return list(dict.fromkeys(suggestions))
            
        except Exception as e:
            print(f"Suggestion scrape error: {e}")
            return []
        finally:
            await browser.close()
