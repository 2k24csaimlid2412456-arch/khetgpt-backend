import os
import random
import requests

API_URL = "http://127.0.0.1:8000/diagnose"
DATA_DIR = os.path.expanduser("~/khetgpt/ml/data/train")
SAMPLES_PER_CLASS = 2
random.seed(1)

classes = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))])

correct_top1 = 0
correct_top3 = 0
total = 0

for cls in classes:
    cls_dir = os.path.join(DATA_DIR, cls)
    files = [f for f in os.listdir(cls_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        continue
    sample = random.sample(files, min(SAMPLES_PER_CLASS, len(files)))

    for fname in sample:
        path = os.path.join(cls_dir, fname)
        with open(path, "rb") as f:
            resp = requests.post(API_URL, files={"file": f})
        if resp.status_code != 200:
            print(f"  ERROR on {path}: {resp.status_code}")
            continue

        preds = resp.json()["predictions"]
        pred_classes = [p["class"] for p in preds]
        total += 1

        if pred_classes[0] == cls:
            correct_top1 += 1
        if cls in pred_classes:
            correct_top3 += 1

        mark = "OK " if pred_classes[0] == cls else "X  "
        print(f"{mark}{cls:30s} -> {pred_classes[0]} ({preds[0]['confidence']*100:.1f}%)")

print(f"\n=== Tested {total} images ===")
print(f"Top-1 accuracy: {correct_top1/total*100:.1f}%")
print(f"Top-3 accuracy: {correct_top3/total*100:.1f}%")
