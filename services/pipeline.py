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
    rule_result = apply_rules(domain, claim_data)
    if len(rule_result) == 3:
        rule_decision, reasons, rule_score = rule_result
    else:
        rule_decision, reasons = rule_result
        rule_score = 90 if rule_decision == "Reject" else 50 if rule_decision == "Needs Review" else 20

    if rule_decision == "Reject":
        fraud_score = _clamp_score(rule_score)
        return {
            "decision": "Reject",
            "fraud_score": fraud_score,
            "explanation": generate_explanation(
                domain,
                fraud_score,
                reasons,
                decision="Reject",
                claim_data=claim_data,
                rule_score=fraud_score,
            ),
            "reasons": reasons,
            "rule_decision": rule_decision,
            "ml_score": None,
            "rule_score": fraud_score,
        }

    rule_score = _clamp_score(rule_score)
    ml_score = _clamp_score(predict_fraud(domain, claim_data))
    final_score = round((rule_score * 0.75) + (ml_score * 0.25), 2)
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
            rule_score=round(rule_score, 2),
            ml_score=round(ml_score, 2),
        ),
        "reasons": reasons,
        "rule_decision": rule_decision,
        "rule_score": round(rule_score, 2),
        "ml_score": round(ml_score, 2),
    }
