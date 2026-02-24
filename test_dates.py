
import requests
import json
import logging
from config import GAMMA_API_BASE, LEAGUE_SERIES_IDS

def test_discovery():
    # Fetch for Premier League (id 14)
    logger = logging.getLogger("test")
    logging.basicConfig(level=logging.INFO)
    
def test_discovery():
    logger = logging.getLogger("test")
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Premier League Discovery (10188)...")
    params = {"series_id": 10188, "closed": "false"}
    try:
        r = requests.get(f"{GAMMA_API_BASE}/events", params=params)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Error fetching 10188: {e}")
        return

    if not data:
        print("No events found.")
        return
    
    print(f"Found {len(data)} Premier League events. Searching for Newcastle:")
    soccer_match = None
    for event in data:
        title = event.get("title", "")
        if "newcastle" in title.lower():
            print(f"MATCH FOUND: {title}")
            soccer_match = event
            break
    
    if soccer_match:
        print(f"\nDumping Newcastle match to event_debug.json")
        with open("event_debug.json", "w", encoding="utf-8") as f:
            json.dump(soccer_match, f, indent=2)
    else:
        print("\nNewcastle match not found.")

if __name__ == "__main__":
    test_discovery()
