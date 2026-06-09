import pandas as pd
import pickle
import os
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

print("🔄 Loading processed dataset...")
df = pd.read_csv("data/processed/features.csv")

# ---------------- FEATURES & TARGET ----------------
X = df.drop("fraud", axis=1)
y = df["fraud"]

# ---------------- TRAIN TEST SPLIT ----------------
# Stratify to ensure train and test sets have the same ratio of fraud
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Compute sample weights for Gradient Boosting since it doesn't support class_weight natively
sample_weights_train = compute_sample_weight(class_weight="balanced", y=y_train)

# ---------------- MODELS DEFINITION ----------------
logistic_model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
rf_model = RandomForestClassifier(n_estimators=150, max_depth=7, min_samples_leaf=4, class_weight="balanced", random_state=42)
gb_model = GradientBoostingClassifier(n_estimators=100, max_depth=4, min_samples_leaf=4, random_state=42)

# Dictionary to store fitted models
trained_models = {}

print("\n🚀 Training cost-sensitive models for imbalanced classes...\n")

# Fit models
print("Training Logistic Regression...")
logistic_model.fit(X_train, y_train)
trained_models["Logistic Regression (Balanced)"] = (logistic_model, None)

print("Training Tuned Random Forest...")
rf_model.fit(X_train, y_train)
trained_models["Random Forest (Balanced, Tuned)"] = (rf_model, None)

print("Training Tuned Gradient Boosting...")
gb_model.fit(X_train, y_train, sample_weight=sample_weights_train)
trained_models["Gradient Boosting (Sample Weighted)"] = (gb_model, None)

best_model = None
best_model_name = ""
best_f1 = 0

print("\n" + "="*80)
print(f"{'MODEL PERFORMANCE EVALUATION (TRAIN vs TEST)':^80}")
print("="*80)

for name, (model, _) in trained_models.items():
    # Predictions
    train_preds = model.predict(X_train)
    train_probs = model.predict_proba(X_train)[:, 1]
    
    test_preds = model.predict(X_test)
    test_probs = model.predict_proba(X_test)[:, 1]

    # Metrics - Train
    tr_acc = accuracy_score(y_train, train_preds)
    tr_prec = precision_score(y_train, train_preds, zero_division=0)
    tr_rec = recall_score(y_train, train_preds)
    tr_f1 = f1_score(y_train, train_preds, zero_division=0)
    tr_auc = roc_auc_score(y_train, train_probs)

    # Metrics - Test
    te_acc = accuracy_score(y_test, test_preds)
    te_prec = precision_score(y_test, test_preds, zero_division=0)
    te_rec = recall_score(y_test, test_preds)
    te_f1 = f1_score(y_test, test_preds, zero_division=0)
    te_auc = roc_auc_score(y_test, test_probs)

    print(f"\n🔹 {name}")
    print(f"  {'Metric':<15} | {'Training Set':<15} | {'Test Set (Unseen)':<15} | {'Status/Gap':<15}")
    print(f"  {'-'*15}-+-{'-'*15}-+-{'-'*15}-+-{'-'*15}")
    print(f"  {'Accuracy':<15} | {tr_acc:<15.4f} | {te_acc:<15.4f} | {abs(tr_acc - te_acc):<15.4f}")
    print(f"  {'Precision':<15} | {tr_prec:<15.4f} | {te_prec:<15.4f} | {abs(tr_prec - te_prec):<15.4f}")
    print(f"  {'Recall':<15} | {tr_rec:<15.4f} | {te_rec:<15.4f} | {abs(tr_rec - te_rec):<15.4f}")
    print(f"  {'F1 Score':<15} | {tr_f1:<15.4f} | {te_f1:<15.4f} | {abs(tr_f1 - te_f1):<15.4f}")
    print(f"  {'ROC-AUC':<15} | {tr_auc:<15.4f} | {te_auc:<15.4f} | {abs(tr_auc - te_auc):<15.4f}")
    
    # Overfitting check comment
    gap = te_f1 - tr_f1
    if abs(gap) < 0.05:
         print("  ℹ️ Overfitting Check: Excellent Generalization (Train and Test F1 are very close)")
    elif gap < -0.15:
         print("  ⚠️ Overfitting Check: Moderate/High Overfitting detected.")
    else:
         print("  ℹ️ Overfitting Check: Normal generalization gap.")

    # Select best model based on Test F1
    if te_f1 > best_f1:
        best_f1 = te_f1
        best_model = model
        best_model_name = name

print("\n" + "="*80)
print(f"🏆 Best Model: {best_model_name} with Test F1 Score of {best_f1:.4f}")
print("="*80)

# ---------------- SAVE BEST MODEL ----------------
os.makedirs("models", exist_ok=True)
with open("models/fraud_model.pkl", "wb") as f:
    pickle.dump(best_model, f)

print(f"\n✅ Best cost-sensitive model saved to models/fraud_model.pkl")