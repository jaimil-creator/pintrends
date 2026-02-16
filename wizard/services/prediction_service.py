import requests
import json
from datetime import datetime, timedelta

class PredictionService:
    def fetch_trends_data(self, keyword):
        # Calculate dates (dynamic based on current time)
        # The legacy code used hardcoded dates, let's make it relative to now for "future prediction" context
        # However, the URL parameters in legacy were specific: end_date=2026-01-30, days=365, etc.
        # Let's stick reasonably close to the legacy URL structure but maybe update the end_date if needed to be "current"
        # actually, the legacy URL has predicted_days=91, implies it gets future data.
        
        # Let's try to use a recent date or just the raw URL structure from legacy if it works.
        # The user said "legacy/test_prediction_fetch.py" has the logic.
        
        
        def get_last_friday(date):
            days_behind = (date.weekday() - 4) % 7
            return date - timedelta(days=days_behind)

        # Start from the most recent Friday
        current_date = get_last_friday(datetime.now())
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        from urllib.parse import quote_plus
        encoded_keyword = quote_plus(keyword)
        
        # Try up to 4 previous Fridays
        for _ in range(4):
            end_date_str = current_date.strftime('%Y-%m-%d')
            url = f"https://trends.pinterest.com/metrics/?terms={encoded_keyword}&country=US&end_date={end_date_str}&days=365&aggregation=2&shouldMock=false&normalize_against_group=true&predicted_days=91"
            
            try:
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]
            except Exception as e:
                print(f"Error fetching for date {end_date_str}: {e}")
            
            # If failed, go back one week
            current_date -= timedelta(weeks=1)
            
        return None
