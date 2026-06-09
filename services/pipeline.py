import uuid
from services.rules.base_rules import apply_rules
from services.ml.prediction import predict_fraud
from decision.decision_engine import make_final_decision
from ocr.parser import parse_and_validate_documents
from services.explanation.generator import generate_explanation
from services.api_client import log_claim

def run_pipeline(domain, claim_data):
    """
    Consolidated Claims Processing Pipeline:
    1. Runs OCR document scanning and extracts data.
    2. Performs real-time field cross-checks for discrepancies.
    3. Runs SQLite database checks & baseline rules.
    4. Runs ML Random Forest predictions.
    5. Computes a consolidated risk score.
    6. Logs the claim transaction in the SQL ledger.
    7. Synthesizes a Gemini RAG Claims Audit Report.
    """
    # ---------------- 1. RUN OCR & VERIFY DOCUMENTS ----------------
    documents = claim_data.get("documents", {})
    ocr_data, ocr_discrepancies, ocr_status = parse_and_validate_documents(documents, domain, claim_data)
    
    # Inject OCR outputs for downstream rules to use (e.g. doctor licenses, plates)
    claim_data["ocr_data"] = ocr_data

    # ---------------- 2. EXECUTE RULE ENGINE ----------------
    rule_decision, reasons = apply_rules(domain, claim_data)

    # ---------------- 3. EXECUTE MACHINE LEARNING ----------------
    ml_score = predict_fraud(domain, claim_data)

    # Adjust ML score if document discrepancies are found (tampering penalty)
    if ocr_discrepancies:
        ml_score = min(100.0, ml_score + 25.0)

    # Convert rule decision to score weights
    if rule_decision == "Reject":
        rule_score = 95.0
    elif rule_decision == "Needs Review":
        rule_score = 50.0
    else:
        rule_score = 15.0

    # ---------------- 4. COMPUTE CONSOLIDATED RISK SCORE ----------------
    # Weighted average: 60% database rules + 40% ML model
    final_score = (rule_score * 0.6) + (ml_score * 0.4)
    final_score = round(final_score, 2)

    # ---------------- 5. DETERMINE VERDICT ----------------
    # Hard Overrides
    if rule_decision == "Reject":
        final_decision = "Reject"
    elif rule_decision == "Needs Review" or ocr_discrepancies:
        final_decision = "Needs Review"
    else:
        # Score-based classification
        if final_score >= 70.0:
            final_decision = "Reject"
        elif final_score >= 40.0:
            final_decision = "Needs Review"
        else:
            final_decision = "Approve"

    # ---------------- 6. LOG TRANSACTION IN LEDGER ----------------
    claim_id = "CLM_" + str(uuid.uuid4())[:8].upper()
    
    # Find Policy Number (depends on form styling)
    policy_no = claim_data.get("policyholder", {}).get("policy_no")
    if not policy_no:
        policy_no = claim_data.get("policy", {}).get("policy_no")
        
    # Find Claim Amount
    claim_amount = 0.0
    if domain == "Health":
        claim_amount = float(claim_data.get("financial", {}).get("total_bill", 0))
    elif domain == "Vehicle":
        claim_amount = float(claim_data.get("damage", {}).get("estimated_cost", 0))
    else:
        claim_amount = float(claim_data.get("financial", {}).get("claim_amount", 0))

    if policy_no:
        log_claim(claim_id, policy_no, claim_amount, final_decision)

    # ---------------- 7. GENERATE AUDIT REPORT ----------------
    explanation = generate_explanation(
        domain=domain,
        claim_data=claim_data,
        rule_decision=rule_decision,
        rule_reasons=reasons,
        ml_score=ml_score,
        ocr_discrepancies=ocr_discrepancies,
        final_decision=final_decision,
        final_score=final_score
    )

    return {
        "claim_id": claim_id,
        "decision": final_decision,
        "fraud_score": final_score,
        "explanation": explanation,
        "ocr_status": ocr_status,
        "ocr_discrepancies": ocr_discrepancies
    }