"""
Maps each disease class to a treatment suggestion and purchase search link.
"""

import urllib.parse

DISEASE_TREATMENTS = {
    "tomato_early_blight": {"treatment": "Chlorothalonil or Mancozeb fungicide spray", "type": "fungicide"},
    "tomato_late_blight": {"treatment": "Metalaxyl + Mancozeb combination fungicide", "type": "fungicide"},
    "tomato_bacterial_spot": {"treatment": "Copper-based bactericide spray", "type": "bactericide"},
    "tomato_septoria_spot": {"treatment": "Chlorothalonil fungicide spray", "type": "fungicide"},
    "tomato_mold": {"treatment": "Improve ventilation + Chlorothalonil spray", "type": "fungicide"},
    "tomato_mosaic_virus": {"treatment": "No cure -- remove infected plants, control aphids/whiteflies", "type": "cultural"},
    "tomato_yellow_virus": {"treatment": "No cure -- control whitefly vectors with Imidacloprid", "type": "insecticide"},
    "tomato_spider_mites": {"treatment": "Miticide spray (e.g. Abamectin) or neem oil", "type": "miticide"},
    "tomato_target_spot": {"treatment": "Azoxystrobin or Chlorothalonil fungicide", "type": "fungicide"},
    "potato_early_blight": {"treatment": "Mancozeb or Chlorothalonil fungicide spray", "type": "fungicide"},
    "potato_late_blight": {"treatment": "Metalaxyl + Mancozeb combination fungicide", "type": "fungicide"},
    "corn_gray_leaf_spot": {"treatment": "Azoxystrobin or Pyraclostrobin fungicide", "type": "fungicide"},
    "corn_leaf_blight": {"treatment": "Propiconazole fungicide spray", "type": "fungicide"},
    "corn_rust": {"treatment": "Propiconazole or Mancozeb fungicide", "type": "fungicide"},
    "grape_black_rot": {"treatment": "Mancozeb or Myclobutanil fungicide spray", "type": "fungicide"},
    "grape_esca": {"treatment": "No chemical cure -- prune infected wood, avoid stress", "type": "cultural"},
    "grape_leaf_blight": {"treatment": "Copper-based fungicide spray", "type": "fungicide"},
    "bellpepper_leaf_spot": {"treatment": "Copper-based bactericide spray", "type": "bactericide"},
    "rice_bacterial_leaf_blight": {"treatment": "Copper oxychloride or Streptocycline spray", "type": "bactericide"},
    "rice_brown_spot": {"treatment": "Mancozeb or Propiconazole fungicide", "type": "fungicide"},
    "rice_hispa": {"treatment": "Chlorpyrifos or Quinalphos insecticide", "type": "insecticide"},
    "rice_leaf_blast": {"treatment": "Tricyclazole fungicide spray", "type": "fungicide"},
    "rice_leaf_scald": {"treatment": "Propiconazole fungicide + balanced fertilization", "type": "fungicide"},
    "rice_narrow_brown_spot": {"treatment": "Mancozeb fungicide spray", "type": "fungicide"},
    "rice_neck_blast": {"treatment": "Tricyclazole fungicide, apply at flowering", "type": "fungicide"},
    "rice_sheath_blight": {"treatment": "Hexaconazole or Validamycin fungicide", "type": "fungicide"},
    "rice_tungro": {"treatment": "No cure -- control leafhopper vectors, use resistant varieties", "type": "cultural"},
    "wheat_septoria": {"treatment": "Propiconazole or Tebuconazole fungicide", "type": "fungicide"},
    "wheat_stripe_rust": {"treatment": "Propiconazole fungicide, apply early", "type": "fungicide"},
}

HEALTHY_CLASSES = {
    "tomato_healthy", "potato_healthy", "corn_healthy", "grape_healthy",
    "bellpepper_healthy", "rice_healthy", "wheat_healthy", "soyabean_healthy",
}


def get_medicine_suggestion(disease_class):
    if disease_class in HEALTHY_CLASSES:
        return {
            "needs_treatment": False,
            "message": "Crop looks healthy -- no treatment needed. Continue regular monitoring.",
        }

    info = DISEASE_TREATMENTS.get(disease_class)
    if not info:
        return {
            "needs_treatment": True,
            "message": "Consult a local agriculture expert for this condition.",
            "treatment": None,
            "purchase_link": None,
        }

    if info["type"] == "cultural":
        return {
            "needs_treatment": True,
            "treatment": info["treatment"],
            "type": info["type"],
            "purchase_link": None,
        }

    query = urllib.parse.quote(info["treatment"].split(" or ")[0].split(" spray")[0])
    purchase_link = f"https://www.amazon.in/s?k={query}"

    return {
        "needs_treatment": True,
        "treatment": info["treatment"],
        "type": info["type"],
        "purchase_link": purchase_link,
    }


if __name__ == "__main__":
    print(get_medicine_suggestion("tomato_early_blight"))
    print(get_medicine_suggestion("wheat_healthy"))
    print(get_medicine_suggestion("rice_tungro"))


# ============================================================
# General crop-input recommendations (herbicides, fertilizers, etc.)
# -- independent of the CNN diagnosis, used for direct farmer questions
# like "what herbicide should I use for weeds in my rice field"
# ============================================================

CROP_INPUTS = {
    ("rice", "weeds"): {
        "products": [
            "Butachlor 50% EC (pre-emergence)",
            "Pretilachlor 50% EC (pre-emergence)",
            "Pendimethalin 30% EC (pre-emergence)",
            "Bispyribac-sodium 10% SC (post-emergence)",
            "Cyhalofop-butyl 10% EC (post-emergence, grassy weeds)",
        ],
        "note": "Pre-emergence options (Butachlor/Pretilachlor within 3-5 days of transplanting, or Pendimethalin within 2-3 days) work best applied early, mixed with sand and broadcast over standing water. If weeds have already emerged, use Bispyribac-sodium or Cyhalofop-butyl instead (effective up to 15-20 days after transplanting). For an organic/non-chemical option, two rounds of manual weeding at 20 and 40 days after transplanting is also effective, especially combined with proper water management to suppress weed germination.",
    },
    ("wheat", "weeds"): {
        "products": ["Isoproturon 75% WP", "Clodinafop 15% WP", "Sulfosulfuron 75% WG"],
        "note": "Apply 30-35 days after sowing for broadleaf and grassy weeds. Clodinafop works well against Phalaris minor (a common wheat weed).",
    },
    ("corn", "weeds"): {
        "products": ["Atrazine 50% WP", "Pendimethalin 30% EC"],
        "note": "Apply Atrazine as pre-emergence within 2-3 days of sowing for effective control.",
    },
    ("general", "weeds"): {
        "products": ["Glyphosate 41% SL"],
        "note": "Non-selective herbicide -- use before sowing/transplanting only, as it kills all vegetation including crops.",
    },
}


CROP_NAME_ALIASES = {
    "dhan": "rice", "chawal": "rice", "paddy": "rice",
    "gehu": "wheat", "gehun": "wheat",
    "makka": "corn", "bhutta": "corn", "maize": "corn",
}


def get_crop_input_suggestion(crop, need="weeds"):
    crop_key = crop.lower().strip()
    crop_key = CROP_NAME_ALIASES.get(crop_key, crop_key)
    key = (crop_key, need.lower().strip())
    info = CROP_INPUTS.get(key) or CROP_INPUTS.get(("general", need.lower().strip()))

    if not info:
        return {"found": False, "message": f"No specific recommendation on file for {need} in {crop}. Consult your local Krishi Vigyan Kendra (KVK)."}

    links = []
    for product in info["products"]:
        query = urllib.parse.quote(product)
        links.append({"product": product, "link": f"https://www.amazon.in/s?k={query}"})

    return {"found": True, "products": links, "note": info["note"]}
