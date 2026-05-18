import numpy as np
import pandas as pd
from services.ml.model_loader import load_model

model = load_model()

FEATURE_COLUMNS = [
    "amount",
    "history",
    "high_amount",
    "frequent_claims",
    "domain_health",
    "domain_vehicle",
    "domain_life",
    "domain_financial",
    "non_network",
    "high_damage",
    "early_policy",
    "income_mismatch",
]

def predict_fraud(domain, data):

    try:

        # =====================================================
        # 🔹 FINANCIAL DOMAIN (UNCHANGED ✅)
        # =====================================================
        if domain == "Financial":

            financial = data.get("financial", {})
            policy = data.get("policy", {})
            docs = data.get("documents", {})

            income = financial.get("income", 0)
            loan = financial.get("loan_amount", 0)
            claim = financial.get("claim_amount", 0)

            emi = policy.get("emi_amount", 0)
            tenure = policy.get("tenure_months", 0)

            if income <= 0 or loan <= 0:
                return 80

            loan_ratio = loan / income
            emi_ratio = emi / income if emi > 0 else 0
            claim_ratio = claim / loan if loan > 0 else 0

            doc_score = sum([
                1 if docs.get("kyc") else 0,
                1 if docs.get("income_proof") else 0,
                1 if docs.get("bank_statement") else 0,
                1 if docs.get("loan_document") else 0
            ]) / 4

            score = 0

            if loan_ratio > 20:
                score += 35
            elif loan_ratio > 10:
                score += 25
            elif loan_ratio > 6:
                score += 15

            if emi_ratio > 0.6:
                score += 35
            elif emi_ratio > 0.4:
                score += 20

            if tenure > 0:
                expected_emi = loan / tenure

                if emi < expected_emi * 0.3:
                    score += 40
                elif emi > expected_emi * 2:
                    score += 20

            if claim > loan:
                score += 35
            elif claim > loan * 0.9:
                score += 15

            score += (1 - doc_score) * 30

            return round(min(score, 100), 2)

        # =====================================================
        # 🔹 VEHICLE DOMAIN (NEW PROFESSIONAL LOGIC ✅)
        # =====================================================
        elif domain == "Vehicle":

            vehicle = data.get("vehicle", {})
            damage = data.get("damage", {})
            incident = data.get("incident", {})
            docs = data.get("documents", {})

            idv = vehicle.get("idv", 0)
            cost = damage.get("estimated_cost", 0)
            accident_type = incident.get("type", "").lower()

            if idv <= 0:
                return 60

            damage_ratio = cost / idv

            doc_score = sum([
                1 if docs.get("rc") else 0,
                1 if docs.get("police") else 0,
                1 if docs.get("images") else 0
            ]) / 3

            score = 0

            # ---------------- CLAIM vs IDV ----------------
            if damage_ratio > 1:
                score += 50
            elif damage_ratio > 0.8:
                score += 25
            elif damage_ratio > 0.5:
                score += 10

            # ---------------- ACCIDENT CONSISTENCY ----------------
            if accident_type == "minor" and damage_ratio > 0.5:
                score += 25

            elif accident_type == "major" and damage_ratio < 0.1:
                score += 10

            # ---------------- DOCUMENT ----------------
            score += (1 - doc_score) * 20

            return round(min(score, 100), 2)

        # =====================================================
        # 🔹 HEALTH + LIFE (UNCHANGED ML)
        # =====================================================
        else:

            if domain == "Health":
                amount = data.get("financial", {}).get("total_bill", 0)
                hospital_network = int(data.get("hospital", {}).get("network", 1))

            elif domain == "Life":
                amount = data.get("financial", {}).get("claim_amount", 0)
                hospital_network = 0

            else:
                amount = 0
                hospital_network = 0

            history = data.get("history", 0)

            high_amount = int(amount > 100000)
            frequent_claims = int(history > 3)

            domain_health = int(domain == "Health")
            domain_vehicle = int(domain == "Vehicle")
            domain_life = int(domain == "Life")
            domain_financial = int(domain == "Financial")

            high_damage = 0

            early_policy = int(
                domain == "Life" and data.get("policy", {}).get("age_years", 1) < 1
            )

            income_mismatch = 0
            non_network = int(hospital_network == 0)

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
            ]], columns=FEATURE_COLUMNS)

            prob = model.predict_proba(features)[0][1]

            return round(prob * 100, 2)

    except Exception as e:
        print("Prediction Error:", e)
        return 10
