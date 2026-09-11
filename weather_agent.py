"""
Weather-risk agent: fetches forecast for a location and computes a simple
disease-risk score based on humidity + temperature (fungal diseases love
high humidity + moderate warmth).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def get_forecast(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def compute_disease_risk(forecast_data):
    """Look at the next ~3 days (8 x 3-hour slots/day = 24 slots) and flag
    fungal-disease risk if humidity stays high with moderate warmth."""
    slots = forecast_data.get("list", [])[:24]
    if not slots:
        return {"risk": "unknown", "reason": "no forecast data"}

    high_humidity_count = 0
    for slot in slots:
        humidity = slot["main"]["humidity"]
        temp = slot["main"]["temp"]
        if humidity > 75 and 20 <= temp <= 30:
            high_humidity_count += 1

    risk_ratio = high_humidity_count / len(slots)

    if risk_ratio > 0.5:
        risk = "high"
        reason = "Extended high humidity + warm temperatures expected -- favorable for fungal diseases (blight, mold, rust)"
    elif risk_ratio > 0.25:
        risk = "moderate"
        reason = "Some periods of high humidity expected -- monitor crops closely"
    else:
        risk = "low"
        reason = "Conditions look unfavorable for major fungal disease spread"

    return {"risk": risk, "reason": reason, "risk_ratio": round(risk_ratio, 2)}


if __name__ == "__main__":
    # Quick test -- Lucknow coordinates (change as needed)
    data = get_forecast(26.8467, 80.9462)
    print(f"City: {data.get('city', {}).get('name')}")
    risk = compute_disease_risk(data)
    print(risk)
