# 🌾 KhetGPT — AI Field Companion for Indian Farmers

KhetGPT is a multi-agent AI platform that unifies crop disease diagnosis,
weather-risk forecasting, live mandi prices, satellite crop-health imagery,
government scheme information, and personalized farming advisory into one
conversational system — in Hindi, English, or Hinglish.

Built for HackIndia Lucknow 2026.

## What It Does

- **Crop Diagnosis**: Upload a leaf photo, get disease detection across 37
  classes (8 crops) with treatment suggestions and purchase links
- **Weather Risk**: Live 5-day forecast-based fungal disease risk assessment
- **Mandi Prices**: Real-time market prices via data.gov.in
- **Satellite Health**: Live NASA satellite imagery (True Color + NDVI)
- **Government Schemes**: RAG-based Q&A over PM-KISAN, PMFBY, KCC, and more
- **Personalized Advisory**: Growth-stage-aware recommendations combining
  weather, mandi, and crop lifecycle data
- **Voice Input**: Hindi/Hinglish voice queries via Web Speech API

## Architecture

An LLM-based orchestrator (Groq + LangChain tool-calling) dynamically routes
each farmer query to the right specialized agent, rather than following a
fixed decision tree. See `orchestrator.py` for the routing logic.

## Tech Stack

**ML**: EfficientNetB0 (fine-tuned CNN), DINOv2 (few-shot fallback), TensorFlow/Keras
**Backend**: FastAPI, SQLite, JWT auth (PyJWT), Pydantic
**LLM/Agents**: LangChain, Groq API (Llama models)
**RAG**: ChromaDB + sentence-transformers
**External APIs**: OpenWeatherMap, data.gov.in Agmarknet, NASA GIBS

## Project Structure
backend/
├── main.py # FastAPI app, all endpoints
├── orchestrator.py # Multi-agent LLM router
├── db.py # Farmer accounts + notifications (SQLite)
├── auth.py # JWT authentication
├── weather_agent.py # Weather-risk calculation
├── mandi_agent.py # Mandi price lookup
├── scheme_agent.py # Government scheme RAG
├── satellite_agent.py # NASA satellite imagery
├── advisory_agent.py # Personalized advisory engine
├── medicine_db.py # Treatment/herbicide database
├── model/ # Trained CNN model + class names
└── requirements.txt

## Setup

1. Clone the repo:
```bash
git clone https://github.com/2k24csaimlid2412456-arch/khetgpt-backend.git
cd khetgpt-backend
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in your own API keys:
```bash
cp .env.example .env
```

## Getting API Keys (all free)

- **Groq**: console.groq.com → API Keys
- **OpenWeatherMap**: openweathermap.org/api
- **data.gov.in**: data.gov.in → Register → My Account → API Key
- **JWT_SECRET**: any random string, e.g. generate with:
```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Running Locally

```bash
python3 -m uvicorn main:app --reload --port 8000
```

The API will be live at `http://127.0.0.1:8000`. Visit `/` for a health check.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/diagnose` | POST | Upload image, get disease diagnosis |
| `/chat` | POST | Conversational multi-agent query |
| `/signup` | POST | Create farmer account |
| `/login` | POST | Authenticate, returns JWT |
| `/profile` | GET/PUT | Farmer profile (auth required) |
| `/advisory` | POST | Personalized advisory (auth required) |
| `/notifications` | GET | Farmer notifications (auth required) |
| `/medicine/{disease_class}` | GET | Treatment lookup |
| `/schemes/list` | GET | All government schemes |
| `/satellite` | GET | NASA satellite imagery URLs |

## Model Performance

The CNN model achieves 85% validation accuracy, and ~75% top-3 / ~47% top-1
accuracy on genuinely unseen real-world photos — measured honestly rather
than only reporting the optimistic validation number. The UI reflects this
by showing top-3 candidates with confidence scores rather than a single
false-certain answer.

## License

Built for HackIndia Lucknow 2026.
