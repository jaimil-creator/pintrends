import asyncio
from typing import List
from .browser import PinterestBrowser
from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime, timedelta

def fetch_trend_prediction(keyword: str, country: str = "US") -> list:
    """
    Fetches prediction data (historical + forecast) from Pinterest API.
    Standalone function to be used by UI or Scraper.
    """
    # Calculate params
    # API requires end_date to be a specific reporting date (usually Fridays).
    # We align to the most recent Friday.
    now = datetime.now()
    # API requires end_date to be a specific reporting date (usually Fridays).
    # We align to the most recent Friday.
    days_to_subtract = (now.weekday() - 4) % 7
    last_friday = now - timedelta(days=days_to_subtract)
    end_date_str = last_friday.strftime("%Y-%m-%d")
    
    # URL Construction
    import urllib.parse
    safe_keyword = urllib.parse.quote_plus(keyword)
    
    url = (
        f"https://trends.pinterest.com/metrics/"
        f"?terms={safe_keyword}"
        f"&country={country}"
        f"&end_date={end_date_str}"
        f"&days=365"
        f"&aggregation=2"
        f"&shouldMock=false"
        f"&normalize_against_group=true"
        f"&predicted_days=91"
    )
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://trends.pinterest.com/"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            
            if isinstance(data, list):
                if len(data) > 0:
                    first_item = data[0]
                    if isinstance(first_item, dict):
                        if "counts" in first_item:
                            return first_item["counts"]
                        elif "data" in first_item:
                            return first_item["data"]
            
            elif isinstance(data, dict):
                if "body" in data and "reports" in data["body"]:
                    reports = data["body"]["reports"]
                    if reports and len(reports) > 0:
                        return reports[0].get("data", [])
                if "counts" in data:
                     return data["counts"]
                     
        else:
            print(f"Prediction API Error: {resp.status_code}")
    except Exception as e:
         print(f"Error fetching predictions: {e}")
         
    return []

class TrendsScraper:
    def __init__(self, headless: bool = False):
        self.browser = PinterestBrowser(headless=headless, auth_file="auth.json")

    def get_trend_prediction(self, keyword: str, country: str = "US") -> list:
        return fetch_trend_prediction(keyword, country)

    async def get_top_trends(
        self, 
        country: str = "US", 
        trend_type: str = "growing",
        interests: list = None,
        ages: list = None,
        genders: list = None
    ) -> List[dict]:
        """
        Navigates to Pinterest Trends and extracts trending keywords.
        """
        # Map trend types to presets
        preset_map = {
            "growing": "3",
            "seasonal": "4",
            "monthly": "1",
            "yearly": "2"
        }
        
        # Interest ID Map
        interest_map = {
            "Animals": "925056443165", "Architecture": "918105274631", "Art": "961238559656",
            "Beauty": "935541271955", "Children's Fashion": "903733943146", "Design": "902065567321",
            "DIY and Crafts": "934876475639", "Education": "922134410098", "Electronics": "960887632144",
            "Entertainment": "953061268473", "Event Planning": "941870572865", "Finance": "913207199297",
            "Food and Drinks": "918530398158", "Gardening": "909983286710", "Health": "898620064290",
            "Home Decor": "935249274030", "Men's Fashion": "924581335376", "Parenting": "920236059316",
            "Quotes": "948192800438", "Sport": "919812032692", "Travel": "908182459161",
            "Vehicles": "918093243960", "Wedding": "903260720461", "Women's Fashion": "948967005229"
        }

        preset = preset_map.get(trend_type.lower(), "3")
        base_url = f"https://trends.pinterest.com/search/?country={country}&trendsPreset={preset}"
        
        # Build URL Filters
        # Example: &l1InterestIds=918105274631%7C961238559656
        filter_params = ""
        
        if interests:
            # Map names to IDs
            valid_ids = [interest_map.get(i) for i in interests if interest_map.get(i)]
            if valid_ids:
                filter_params += f"&l1InterestIds={'%7C'.join(valid_ids)}"
        
        if ages:
            # ageBucket=18-24%7C25-34
            filter_params += f"&ageBucket={'%7C'.join(ages)}"
            
        if genders:
            # gender=female%7Cmale
            filter_params += f"&gender={'%7C'.join(genders)}"
            
        final_url = base_url + filter_params
        
        print(f"Navigating to {final_url}...")
        
        await self.browser.start()
        try:
            await self.browser.navigate(final_url)
            
            # Wait for content to load.
            await asyncio.sleep(8) 
            
            html = await self.browser.get_content()
            soup = BeautifulSoup(html, "html.parser")
            
            trends = []
            
            # Extract logic:
            # Look for elements that likely contain the trend keywords.
            # In the table, they are often in <div> or <a> tags with specific classes.
            # A common pattern is text inside 'div[data-test-id="trend-card"]' or similar.
            # Since classes change, we might look for the table rows.
            
            # Fallback/General strategy: finding the list of terms.
            # Often they are inside links that match /trends/
            
            # Trying to find the "Top trends" or similar section.
            # We will grab any text that looks like a keyword from the main area.
            
            # Debug: dump some text to see what we got if needed.
            # For now, let's try a broad extraction of the table text.
            
            # Heuristic: Trends table usually has rank (1, 2, 3...) next to a keyword.
            # Let's simple scrape all text and look for the table structure? No, too messy.
            
            # Better: Look for A tags that link to /trends/...
            # e.g. https://www.pinterest.com/trends/term/... (Wait, trends.pinterest.com might use different links)
            
            # Current Trends UI typically has a list on the left or bottom.
            # Let's try to find text elements with a specific class or structure.
            # Example: Role="row" -> extract text.
            
            # Extract using validated selectors from debug_trends.html
            print("Extracting trends from table...")
            
            # The structure is a table-like grid. 
            # We iterate over rows which contain the term and the metrics.
            # Based on debug_trends.html, it seems we can find rows or just iterate through terms and find siblings?
            # Actually, "trends-table-term" is in a cell. The metrics are in following cells.
            # Best approach: Find the row (tr) or common container.
            # In HTML: tr -> td -> div[data-test-id="trends-table-term"]
            # Sibling td -> div[data-test-id="filterable-box-cell-wow"]
            
            # Let's find all rows first.
            rows = soup.find_all("tr")
            
            for row in rows:
                try:
                    # Find keyword
                    keyword_div = row.find("div", {"data-test-id": "trends-table-term"})
                    if not keyword_div:
                        continue
                        
                    keyword = keyword_div.get_text(strip=True)
                    if not keyword:
                        continue
                        
                    # Find metrics
                    # Helper to safely get text
                    def get_metric(test_id):
                        div = row.find("div", {"data-test-id": test_id})
                        return div.get_text(strip=True) if div else None
                        
                    wow = get_metric("filterable-box-cell-wow")
                    mom = get_metric("filterable-box-cell-mom")
                    yoy = get_metric("filterable-box-cell-yoy")
                    
                    trends.append({
                        "keyword": keyword,
                        "weekly_change": wow,
                        "monthly_change": mom,
                        "yearly_change": yoy
                    })
                    
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
            
            print(f"Found {len(trends)} trends.")
            
            if not trends:
               print("Debug warning: No trends found with primary selector. Dump saved.")
            
            # Preserve order while removing duplicates (by keyword)
            unique_trends = []
            seen_keywords = set()
            for t in trends:
                if t["keyword"] not in seen_keywords:
                    unique_trends.append(t)
                    seen_keywords.add(t["keyword"])
                    
            return unique_trends
            
        finally:
            await self.browser.close()

if __name__ == "__main__":
    scraper = TrendsScraper(headless=False)
    trends = asyncio.run(scraper.get_top_trends())
    print(f"Trends Found: {trends}")
