import numpy as np
from services.ml.model_loader import load_model
from services.api_client import get_claim_history_count

try:
    model = load_model()
except Exception as e:
    print("Error loading ML model in prediction.py:", e)
    model = None

def predict_fraud(domain, data):
    """
    Computes a ML-based fraud risk probability (0-100) using the trained Random Forest classifier.
    Unifies all domains by mapping their fields into the standard feature set.
    """
    if model is None:
        print("⚠️ ML model not loaded, returning default baseline score.")
        return 15.0

    try:
        # ---------------- 1. RESOLVE DYNAMIC POLICY HISTORY ----------------
        policy_no = data.get("policyholder", {}).get("policy_no")
        if not policy_no:
            policy_no = data.get("policy", {}).get("policy_no", "")
            
        history = get_claim_history_count(policy_no)

        # ---------------- 2. INITIALIZE FEATURES ----------------
        amount = 0.0
        
        domain_health = int(domain == "Health")
        domain_vehicle = int(domain == "Vehicle")
        domain_life = int(domain == "Life")
        domain_financial = int(domain == "Financial")
        
        non_network = 0
        high_damage = 0
        early_policy = 0
        income_mismatch = 0

        # ---------------- 2. DOMAIN-SPECIFIC MAPPINGS ----------------
        if domain == "Health":
            amount = float(data.get("financial", {}).get("total_bill", 0))
            network = data.get("hospital", {}).get("network", True)
            non_network = int(not network)

        elif domain == "Vehicle":
            amount = float(data.get("damage", {}).get("estimated_cost", 0))
            high_damage = int(amount > 50000)

        elif domain == "Life":
            amount = float(data.get("financial", {}).get("claim_amount", 0))
            
            # Policy Duration (Years)
            policy_duration = float(data.get("policy", {}).get("duration", 2.0))
            early_policy = int(policy_duration < 1.0)

        elif domain == "Financial":
            amount = float(data.get("financial", {}).get("claim_amount", 0))
            loan_amount = float(data.get("financial", {}).get("loan_amount", 0))
            income = float(data.get("financial", {}).get("income", 1.0))
            
            # Income check (avoid division by zero)
            income_mismatch = int(loan_amount > income * 5)

        # ---------------- 3. CORE LOGIC FEATURES ----------------
        high_amount = int(amount > 100000)
        frequent_claims = int(history > 3)

        import pandas as pd

        # ---------------- 4. CONSTRUCT FEATURE DATAFRAME ----------------
        # Order and names must match preprocessing columns
        feature_names = [
            "amount", "history", "high_amount", "frequent_claims",
            "domain_health", "domain_vehicle", "domain_life", "domain_financial",
            "non_network", "high_damage", "early_policy", "income_mismatch"
        ]
        features = pd.DataFrame([[ 
            amount,
            history,
            high_amount,
            frequent_claims,
            domain_health,
            domain_vehicle,
            domain_life,
            domain_financial,
            non_network,
            high_damage,
            early_policy,
            income_mismatch
        ]], columns=feature_names)

        # ---------------- 5. RUN PREDICTION ----------------
        prob = model.predict_proba(features)[0][1]
        score = round(prob * 100, 2)
        
        # Safety Clamping
        return max(0.0, min(100.0, score))

    except Exception as e:
        print("Prediction Error in ML model:", e)
        return 20.0