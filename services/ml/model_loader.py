import pickle
from pathlib import Path


MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "fraud_model.pkl"

def load_model():
    with MODEL_PATH.open("rb") as f:
        model = pickle.load(f)
    return model
