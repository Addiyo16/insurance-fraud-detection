from services.rules.base_rules import apply_rules
from services.ml.prediction import predict_fraud
from decision.decision_engine import make_decision, make_final_decision
from utils.helpers import add_claim_history


def run_pipeline(domain, claim_data):

    # ---------------- RULE ENGINE ----------------
    rule_decision, reasons = apply_rules(domain, claim_data)

    # 🔴 HARD OVERRIDE (INDUSTRY)
    if rule_decision == "Reject":
        return {
            "decision": "Reject",
            "fraud_score": 90,
            "explanation": "\n".join(reasons)
        }

    # ---------------- RULE SCORE ----------------
    if rule_decision == "Needs Review":
        rule_score = 50
    else:
        rule_score = 20

    # ---------------- ML ----------------
    ml_score = predict_fraud(domain, claim_data)

    # 🧠 SAFETY CLAMP (NEW - IMPORTANT)
    if ml_score < 0:
        ml_score = 0
    elif ml_score > 100:
        ml_score = 100

    # ---------------- FINAL SCORE ----------------
    final_score = (rule_score * 0.6) + (ml_score * 0.4)

    # ---------------- FINAL DECISION ----------------
    decision = make_final_decision(final_score, rule_decision)

    # ---------------- STORE HISTORY ----------------
    if domain == "Financial":
        loan_id = claim_data.get("policy", {}).get("loan_id")
        if loan_id:
            add_claim_history(loan_id)

    return {
        "decision": decision,
        "fraud_score": round(final_score, 2),
        "explanation": "\n".join(reasons)
    }