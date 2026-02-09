import joblib
import pandas as pd
from pathlib import Path

# Get project root directory safely
BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = BASE_DIR / "ml" / "artifacts" / "best_fraud_pipeline.pkl"

_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = joblib.load(MODEL_PATH)
    return _pipeline

def predict_fraud(data):
    df = pd.DataFrame([data])
    model = get_pipeline()
    prediction = model.predict(df)[0]
    probability = model.predict_proba(df)[0][1]
    return prediction, probability

