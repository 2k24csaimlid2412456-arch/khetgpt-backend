"""
Mandi price agent: fetches current market prices for a crop from
data.gov.in's Agmarknet dataset (Current Daily Price of Various Commodities).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY")

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"

# data.gov.in blocks/drops requests without a browser-like User-Agent
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def get_mandi_price(commodity, state=None, limit=10):
    url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
    params = {
        "api-key": DATA_GOV_API_KEY,
        "format": "json",
        "limit": limit,
        "filters[commodity]": commodity,
    }
    if state:
        params["filters[state]"] = state

    resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    records = data.get("records", [])
    if not records:
        return {"commodity": commodity, "found": False, "message": "No recent price data found"}

    return {"commodity": commodity, "found": True, "records": records}


if __name__ == "__main__":
    result = get_mandi_price("Wheat", state="Uttar Pradesh")
    print(result)
