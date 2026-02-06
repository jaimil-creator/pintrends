import requests
import json
from datetime import datetime, timedelta

def test_dates():
    base_url = "https://trends.pinterest.com/metrics/?terms=old+lady+costume&country=US&days=365&aggregation=2&shouldMock=false&normalize_against_group=true&predicted_days=91"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    dates_to_test = ["2026-01-30", "2026-02-04"] # Friday vs Wednesday
    
    for d in dates_to_test:
        url = f"{base_url}&end_date={d}"
        print(f"Testing {d}...")
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                has_data = len(data) > 0 and 'counts' in data[0]
                print(f"[{d}] Success: {has_data}")
            else:
                print(f"[{d}] Failed: {resp.status_code}")
        except Exception as e:
            print(f"[{d}] Error: {e}")

if __name__ == "__main__":
    test_dates()
