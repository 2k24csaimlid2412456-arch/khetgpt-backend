"""
Personalized advisory engine: combines a farmer's crop growth stage,
current weather risk, and mandi price into an LLM-generated, personalized
recommendation.
"""

import os
from datetime import datetime, date
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from weather_agent import get_forecast, compute_disease_risk
from mandi_agent import get_mandi_price

load_dotenv()
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3, groq_api_key=os.getenv("GROQ_API_KEY"))

# Generic growth-stage windows (days since sowing) -- approximation that
# works reasonably across common crops like wheat, rice, corn.
GROWTH_STAGES = [
    (0, 15, "Germination / Seedling"),
    (15, 40, "Vegetative Growth"),
    (40, 70, "Flowering / Reproductive"),
    (70, 100, "Grain Filling / Maturation"),
    (100, 999, "Harvest Ready"),
]


def estimate_growth_stage(sowing_date_str):
    if not sowing_date_str:
        return {"days_since_sowing": None, "stage": "Unknown -- sowing date not set"}

    sowing_date = datetime.strptime(sowing_date_str, "%Y-%m-%d").date()
    days = (date.today() - sowing_date).days

    for low, high, stage_name in GROWTH_STAGES:
        if low <= days < high:
            return {"days_since_sowing": days, "stage": stage_name}

    return {"days_since_sowing": days, "stage": "Harvest Ready"}


def generate_advisory(farmer):
    growth = estimate_growth_stage(farmer.get("sowing_date"))

    weather_summary = "Weather data unavailable"
    try:
        lat = farmer.get("lat") or 26.8467
        lon = farmer.get("lon") or 80.9462
        forecast = get_forecast(lat, lon)
        risk = compute_disease_risk(forecast)
        weather_summary = f"{risk['risk']} disease risk -- {risk['reason']}"
    except Exception:
        pass

    mandi_summary = "Mandi price data unavailable"
    try:
        crop = farmer.get("crop", "wheat").title()
        result = get_mandi_price(crop, state=farmer.get("state", "Uttar Pradesh"))
        if result["found"]:
            price = result["records"][0]["modal_price"]
            mandi_summary = f"Rs {price}/quintal in {farmer.get('state', 'your state')}"
    except Exception:
        pass

    prompt = f"""Farmer profile:
- Crop: {farmer.get('crop', 'not specified')}
- Land size: {farmer.get('land_size_acres', 'not specified')} acres
- Growth stage: {growth['stage']} (Day {growth['days_since_sowing']} since sowing)
- Location: {farmer.get('district', '')}, {farmer.get('state', '')}
- Current weather risk: {weather_summary}
- Current mandi price: {mandi_summary}

Write a short (3-4 sentences), practical, personalized advisory for this
farmer in simple Hinglish (Hindi-English mix). Cover: what to watch for at
this growth stage, any weather-related precaution, and one actionable tip.
Keep it warm and direct, like advice from a knowledgeable friend."""

    response = llm.invoke([
        SystemMessage(content="You are KhetGPT, an agricultural advisor for Indian farmers."),
        HumanMessage(content=prompt)
    ])

    return {
        "growth_stage": growth,
        "weather_summary": weather_summary,
        "mandi_summary": mandi_summary,
        "advisory": response.content,
    }


if __name__ == "__main__":
    test_farmer = {
        "crop": "wheat",
        "land_size_acres": 5,
        "sowing_date": "2026-07-01",
        "district": "Lucknow",
        "state": "Uttar Pradesh",
    }
    result = generate_advisory(test_farmer)
    print(result)
