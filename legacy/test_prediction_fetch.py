import requests
import json
from datetime import datetime, timedelta

def test_fetch():
    # User provided URL
    url = "https://trends.pinterest.com/metrics/?terms=old+lady+costume&country=US&end_date=2026-01-30&days=365&aggregation=2&shouldMock=false&normalize_against_group=true&predicted_days=91"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        print(f"Fetching {url}...")
        resp = requests.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print("Success! Data keys:")
            if isinstance(data, list) and len(data) > 0:
                print(data[0].keys())
                print(f"Counts: {len(data[0].get('counts', []))}")
            else:
                print("Data format unexpected:", data)
        else:
            print(f"Error: {resp.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_fetch()
