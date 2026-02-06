import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_api():
    print("Checking API health...")
    try:
        r = requests.get(f"{BASE_URL}/")
        print(f"Root: {r.json()}")
    except Exception as e:
        print(f"API not reachable: {e}")
        return

    keyword = "test api keyword"
    print(f"\nAnalyzing keyword: {keyword}")
    r = requests.post(f"{BASE_URL}/analyze-keyword", json={"keyword": keyword, "force_rescrape": True})
    print(f"Analyze Reponse: {r.json()}")
    
    print("Waiting for background job to finish (45s)...")
    time.sleep(45)
    
    print("\nGetting Results...")
    r = requests.get(f"{BASE_URL}/keyword/{keyword}")
    if r.status_code == 200:
        data = r.json()
        print(f"Keyword: {data['keyword']}")
        print(f"Score: {data['current_score']} ({data['bucket']})")
        print(f"Pins Found: {len(data['pins'])}")
    else:
        print(f"Error: {r.status_code} - {r.text}")

if __name__ == "__main__":
    test_api()
