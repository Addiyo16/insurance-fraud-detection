import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

print("🔄 Loading processed dataset...")
df = pd.read_csv("data/processed/features.csv")

# ---------------- FEATURES & TARGET ----------------
X = df.drop("fraud", axis=1)
y = df["fraud"]

# ---------------- TRAIN TEST SPLIT ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ---------------- MODELS ----------------
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Random Forest": RandomForestClassifier(n_estimators=100)
}

best_model = None
best_f1 = 0

print("\n🚀 Training models...\n")

for name, model in models.items():

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds)
    rec = recall_score(y_test, preds)
    f1 = f1_score(y_test, preds)

    print(f"🔹 {name}")
    print(f"Accuracy  : {acc:.4f}")
    print(f"Precision : {prec:.4f}")
    print(f"Recall    : {rec:.4f}")
    print(f"F1 Score  : {f1:.4f}")
    print("-" * 30)

    # Select best model based on F1
    if f1 > best_f1:
        best_f1 = f1
        best_model = model

# ---------------- SAVE BEST MODEL ----------------
pickle.dump(best_model, open("models/fraud_model.pkl", "wb"))

print("\n✅ Best model saved to models/fraud_model.pkl")