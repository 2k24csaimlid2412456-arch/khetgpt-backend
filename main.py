from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
from PIL import Image
import numpy as np
import json
import io
import os

app = FastAPI(title="KhetGPT Diagnosis API")

# Allow frontend (running on any origin) to call this API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "khetgpt_cnn_model.h5")
CLASSES_PATH = os.path.join(os.path.dirname(__file__), "model", "class_names.json")

print("Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)
with open(CLASSES_PATH) as f:
    class_names = json.load(f)
print(f"Model loaded. {len(class_names)} classes ready.")


def preprocess_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((224, 224))
    arr = np.array(img, dtype=np.float32)
    arr = np.expand_dims(arr, axis=0)  # add batch dimension
    return arr


@app.get("/")
def root():
    return {"status": "KhetGPT API is running", "classes_loaded": len(class_names)}


import colorsys


def leaf_likelihood_score(image: Image.Image) -> float:
    """Rough heuristic: fraction of pixels in green/brown/yellow hue ranges
    typical of plant leaves. Flags photos that likely aren't crop leaves at
    all (people, animals, objects) before trusting the forced 37-class prediction."""
    small = image.convert("RGB").resize((48, 48))
    pixels = list(small.getdata())
    leafish = 0.0
    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        hue_deg = h * 360
        if s > 0.15 and 0.08 < v < 0.97:
            if 60 <= hue_deg <= 170:
                leafish += 1.0
            elif 20 <= hue_deg < 60:
                leafish += 0.5
    return leafish / len(pixels)


@app.post("/diagnose")
async def diagnose(file: UploadFile = File(...)):
    image_bytes = await file.read()
    arr = preprocess_image(image_bytes)

    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    leaf_score = leaf_likelihood_score(pil_image)

    predictions = model.predict(arr, verbose=0)[0]
    top_indices = predictions.argsort()[-3:][::-1]

    results = [
        {"class": class_names[i], "confidence": float(predictions[i])}
        for i in top_indices
    ]

    # Stage 2/3: decompose the flat 37-class prediction into a two-stage
    # reading -- crop confidence = sum of all disease-variant probabilities
    # for that crop, disease confidence = conditional on the crop being correct.
    crop_totals = {}
    for i, cname in enumerate(class_names):
        crop = cname.split("_")[0]
        crop_totals[crop] = crop_totals.get(crop, 0.0) + float(predictions[i])

    top_class = results[0]["class"]
    top_confidence = results[0]["confidence"]
    top_crop = top_class.split("_")[0]
    disease_part = "_".join(top_class.split("_")[1:]) or "unknown"

    crop_confidence = crop_totals.get(top_crop, top_confidence)
    disease_confidence = top_confidence / crop_confidence if crop_confidence > 0 else top_confidence

    stage1_passed = leaf_score >= 0.10
    warning = None
    if not stage1_passed:
        warning = "This photo doesn't look like a clear crop leaf image. For accurate results, upload a well-lit photo of a single leaf filling most of the frame."
    elif top_confidence < 0.30:
        warning = "Confidence is low for this result. Try a clearer, closer photo of a single affected leaf for a more reliable diagnosis."

    return {
        "filename": file.filename,
        "pipeline": {
            "image_validation": {"passed": stage1_passed, "leaf_likelihood": round(leaf_score, 3)},
            "crop_classification": {"crop": top_crop, "confidence": round(crop_confidence, 3)},
            "disease_classification": {"disease": disease_part, "confidence": round(disease_confidence, 3)},
        },
        "predictions": results,
        "leaf_likelihood": round(leaf_score, 3),
        "warning": warning,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


from pydantic import BaseModel
from orchestrator import chat as orchestrator_chat


from typing import List, Optional

class ChatTurn(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatTurn]] = None


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    history = [turn.model_dump() for turn in request.history] if request.history else None
    response = orchestrator_chat(request.message, history=history)
    return {"response": response}


from satellite_agent import get_satellite_urls


@app.get("/satellite")
def satellite(lat: float = 26.8467, lon: float = 80.9462):
    urls = get_satellite_urls(lat, lon)
    return {"lat": lat, "lon": lon, **urls}


# ============================================================
# Farmer Authentication & Profile (JWT-based)
# ============================================================

from fastapi import Depends, HTTPException
from typing import Optional
import db as db_module
from auth import create_token, get_current_farmer


class SignupRequest(BaseModel):
    username: str
    password: str
    land_size_acres: Optional[float] = None
    crop: Optional[str] = None
    sowing_date: Optional[str] = None  # ISO format: YYYY-MM-DD
    state: Optional[str] = None
    district: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ProfileUpdateRequest(BaseModel):
    land_size_acres: Optional[float] = None
    crop: Optional[str] = None
    sowing_date: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


@app.post("/signup")
def signup(req: SignupRequest):
    if len(req.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    farmer_id = db_module.create_farmer(
        username=req.username.strip(),
        password=req.password,
        land_size_acres=req.land_size_acres,
        crop=req.crop,
        sowing_date=req.sowing_date,
        state=req.state,
        district=req.district,
        lat=req.lat,
        lon=req.lon,
    )
    if farmer_id is None:
        raise HTTPException(status_code=400, detail="Username already taken")

    token = create_token(farmer_id, req.username.strip())
    return {"token": token, "farmer_id": farmer_id}


@app.post("/login")
def login(req: LoginRequest):
    farmer = db_module.verify_login(req.username.strip(), req.password)
    if farmer is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(farmer["id"], farmer["username"])
    return {"token": token, "farmer_id": farmer["id"]}


@app.get("/profile")
def get_profile(current=Depends(get_current_farmer)):
    farmer = db_module.get_farmer(current["farmer_id"])
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    farmer.pop("password_hash", None)
    farmer.pop("salt", None)
    return farmer


@app.put("/profile")
def update_profile(req: ProfileUpdateRequest, current=Depends(get_current_farmer)):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    db_module.update_farmer(current["farmer_id"], **updates)
    return {"status": "updated"}


# ============================================================
# Personalized Advisory + Medicine Suggestions
# ============================================================

from advisory_agent import generate_advisory
from medicine_db import get_medicine_suggestion


@app.post("/advisory")
def get_advisory(current=Depends(get_current_farmer)):
    farmer = db_module.get_farmer(current["farmer_id"])
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    result = generate_advisory(farmer)

    db_module.add_notification(
        farmer["id"], "advisory",
        f"[{result['growth_stage']['stage']}] {result['advisory'][:150]}..."
    )

    return result


@app.get("/medicine/{disease_class}")
def medicine_lookup(disease_class: str):
    return get_medicine_suggestion(disease_class)


@app.get("/notifications")
def notifications(current=Depends(get_current_farmer)):
    return db_module.get_notifications(current["farmer_id"])


# ============================================================
# Government Schemes listing
# ============================================================

from scheme_agent import SCHEMES


@app.get("/schemes/list")
def list_schemes():
    return SCHEMES


# ============================================================
# Startup: ensure databases exist on any fresh deployment
# ============================================================

import scheme_agent


@app.on_event("startup")
def on_startup():
    db_module.init_db()
    scheme_agent.build_index()
    print("Startup complete: farmer DB + scheme DB ready")
