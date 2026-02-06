import asyncio
from typing import List
from .browser import PinterestBrowser
from bs4 import BeautifulSoup
import re

class SuggestionsScraper:
    def __init__(self, headless: bool = False):
        self.browser = PinterestBrowser(headless=headless, auth_file="auth.json")

    async def get_suggestions(self, keyword: str) -> List[str]:
        """
        Navigates to search results and extracts related/guided search terms.
        """
        # Ensure browser is started
        if not self.browser.page:
            await self.browser.start()
        
        page = self.browser.page
        
        try:
            # 1. Navigate to Search Result Page
            # URL: https://www.pinterest.com/search/pins/?q=valentines%20nails&rs=typed
            search_url = f"https://www.pinterest.com/search/pins/?q={keyword}&rs=typed"
            print(f"Fetching suggestions from: {search_url}")
            
            await self.browser.navigate(search_url)
            # Wait for bubbles to load
            await asyncio.sleep(4)
            
            suggestions = []
            
            # 2. Extract Suggestions using User's Selector
            # Selector: .KvKvqR > div > div
            # Warning: Obfuscated class names like .KvKvqR change frequently.
            
            # Using user provided selector
            print("Using user selector: .KvKvqR > div > div")
            results = page.locator('.KvKvqR > div > div')
            count = await results.count()
            
            if count == 0:
                 print("Debug: User selector returned 0. Trying fallbacks.")
                 # Fallback matches common "Related Search" pills
                 # Try finding elements that look like pills at the top
                 # data-test-id="guided-search-guide" is a known ID for these bubbles
                 results = page.locator('[data-test-id="guided-search-guide"]')
                 count = await results.count()

            print(f"Debug: Found {count} suggestion bubbles.")

            for i in range(count):
                text = await results.nth(i).text_content()
                if text:
                    raw_text = text.strip()
                    # Apply formatting: Insert comma between lowercase and Uppercase (CamelCase split)
                    # "ideasDesigns" -> "ideas, Designs"
                    formatted_text = re.sub(r'(?<=[a-z])(?=[A-Z])', ', ', raw_text)
                    suggestions.append(formatted_text)
            
            if not suggestions:
                print("Debug: No suggestions found. Saving debug_suggestions.html")
                content = await page.content()
                with open("debug_suggestions.html", "w", encoding="utf-8") as f:
                    f.write(content)

            return list(dict.fromkeys(suggestions))
            
        except Exception as e:
            print(f"Error getting suggestions for {keyword}: {e}")
            return []

    async def close(self):
        await self.browser.close()
