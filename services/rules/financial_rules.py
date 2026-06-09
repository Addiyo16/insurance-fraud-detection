from services.api_client import get_policy_details, get_loan_details, get_claim_history_count, check_duplicate_claim

def run(data):
    reasons = []
    decision = "Approve"
    risk_score = 0

    # ---------------- EXTRACT FIELDS ----------------
    policy_no = data.get("policy", {}).get("policy_no", "").strip()
    loan_id = data.get("policy", {}).get("loan_id", "").strip()
    
    financial = data.get("financial", {})
    income = financial.get("income", 0)
    loan_amount_input = financial.get("loan_amount", 0)
    claim_amount = financial.get("claim_amount", 0)

    # ---------------- 1. REGISTRY POLICY CHECK ----------------
    if not policy_no:
        return "Reject", ["Policy number is required for validation."]
        
    registry_policy = get_policy_details(policy_no)
    if not registry_policy:
        return "Reject", [f"Invalid Policy Number '{policy_no}': Record not found in registry."]
        
    if registry_policy["status"].lower() != "active":
        return "Reject", [f"Policy '{policy_no}' is currently {registry_policy['status']}."]

    # DYNAMIC DUPLICATE CLAIM CHECK
    if claim_amount > 0 and check_duplicate_claim(policy_no, claim_amount):
        return "Reject", [f"Claim Rejected: A credit default claim for the exact same amount (${claim_amount}) already exists under Policy '{policy_no}'."]

    # DYNAMIC HISTORY CHECK
    history_count = get_claim_history_count(policy_no)
    if history_count >= 3:
        reasons.append(f"⚠ High claim frequency: Policyholder has {history_count} previous financial claims logged in the database registry.")
        risk_score += 25

    # Check Credit Score
    credit_score = registry_policy.get("credit_score", 700)
    if credit_score < 500:
        reasons.append(f"⚠ Critical credit score found in registry: {credit_score} (High default risk).")
        risk_score += 35
    elif credit_score < 600:
        reasons.append(f"Low credit score found in registry: {credit_score}.")
        risk_score += 15

    # ---------------- 2. LOAN CONTRACT REGISTRY CHECK ----------------
    if not loan_id:
        reasons.append("⚠ Loan ID is missing from claim submission.")
        risk_score += 25
    else:
        loan_record = get_loan_details(loan_id)
        if not loan_record:
            return "Reject", [f"Claim Rejected: Loan ID '{loan_id}' is invalid or not registered in the loan directory."]
            
        # Verify loan policy linkage
        if loan_record["policy_number"] != policy_no:
            return "Reject", [f"Claim Rejected: Loan ID '{loan_id}' is not registered under Policy '{policy_no}'."]
            
        # Verify loan amount mismatch
        reg_loan_amount = loan_record["loan_amount"]
        if loan_amount_input > 0 and abs(loan_amount_input - reg_loan_amount) > 100:
            reasons.append(f"⚠ Loan amount mismatch: UI declared ${loan_amount_input} vs Registry Contract ${reg_loan_amount}")
            risk_score += 25

    # ---------------- 3. FINANCIAL RATIOS & HEURISTICS ----------------
    if income <= 0:
        return "Needs Review", ["Monthly income must be greater than zero."]

    # Debt-to-Income / FOIR
    emi = data.get("policy", {}).get("emi_amount", 0)
    if emi > 0:
        dti_ratio = emi / income
        if dti_ratio > 0.6:
            reasons.append(f"⚠ High DTI Ratio: EMI payments exceed {dti_ratio:.0%} of monthly income.")
            risk_score += 30
        elif dti_ratio > 0.4:
            reasons.append(f"Moderate DTI Ratio: EMI payments are {dti_ratio:.0%} of monthly income.")
            risk_score += 15

    # Claim ratio
    if claim_amount > loan_amount_input:
        return "Reject", [f"Claim amount (${claim_amount}) cannot exceed the outstanding loan amount (${loan_amount_input})."]

    claim_ratio = claim_amount / loan_amount_input if loan_amount_input > 0 else 0
    if claim_ratio > 0.9:
        reasons.append("Full coverage loan claim (high risk closeout).")
        risk_score += 20

    # ---------------- 4. FINAL SCORE AGGREGATION ----------------
    if risk_score >= 80:
        decision = "Reject"
    elif risk_score >= 40:
        decision = "Needs Review"
    else:
        decision = "Approve"

    if not reasons:
        reasons.append("All financial registry and debt ratio checks passed.")

    return decision, reasons