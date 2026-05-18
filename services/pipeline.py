from services.rules.base_rules import apply_rules
from services.ml.prediction import predict_fraud
from decision.decision_engine import make_final_decision
from services.explanation.generator import generate_explanation
from utils.helpers import add_claim_history


def _clamp_score(score):
    try:
        return max(0, min(100, float(score)))
    except (TypeError, ValueError):
        return 0


def run_pipeline(domain, claim_data):
    rule_decision, reasons = apply_rules(domain, claim_data)

    if rule_decision == "Reject":
        fraud_score = 90
        return {
            "decision": "Reject",
            "fraud_score": fraud_score,
            "explanation": generate_explanation(
                domain,
                fraud_score,
                reasons,
                decision="Reject",
                claim_data=claim_data,
            ),
            "reasons": reasons,
            "rule_decision": rule_decision,
            "ml_score": None,
        }

    rule_score = 50 if rule_decision == "Needs Review" else 20
    ml_score = _clamp_score(predict_fraud(domain, claim_data))
    final_score = round((rule_score * 0.6) + (ml_score * 0.4), 2)
    decision = make_final_decision(final_score, rule_decision)

    if domain == "Financial":
        loan_id = claim_data.get("policy", {}).get("loan_id")
        if loan_id:
            add_claim_history(loan_id)

    return {
        "decision": decision,
        "fraud_score": final_score,
        "explanation": generate_explanation(
            domain,
            final_score,
            reasons,
            decision=decision,
            claim_data=claim_data,
        ),
        "reasons": reasons,
        "rule_decision": rule_decision,
        "ml_score": round(ml_score, 2),
    }
