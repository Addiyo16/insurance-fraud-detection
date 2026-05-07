import pickle
import os

# create models folder if not exists
os.makedirs("models", exist_ok=True)

# dummy data (later replace with your ML model)
data = {"project": "fraud detection"}

# save as .pkl
with open("models/fraud_model.pkl", "wb") as f:
    pickle.dump(data, f)

print("fraud_model.pkl created successfully!")