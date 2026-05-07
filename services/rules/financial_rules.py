def run(data):

    reasons = []
    decision = "Approve"
    risk_score = 0

    financial = data.get("financial", {})
    policy = data.get("policy", {})
    docs = data.get("documents", {})
    history = data.get("history", 0)

    income = financial.get("income", 0)              # monthly
    loan = financial.get("loan_amount", 0)
    claim = financial.get("claim_amount", 0)

    emi = policy.get("emi_amount", 0)
    tenure = policy.get("tenure_months", 0)
    policy_age = policy.get("age_months", 12)

    # =====================================================
    # 🔹 1. BASIC VALIDATION
    # =====================================================
    if income <= 0 or loan <= 0:
        return "Needs Review", ["Invalid income or loan amount"]

    # =====================================================
    # 🔹 2. DOCUMENT VALIDATION
    # =====================================================
    required_docs = ["kyc", "income_proof", "bank_statement", "loan_document"]
    missing = [d for d in required_docs if not docs.get(d)]

    if missing:
        return "Needs Review", [f"Missing documents: {', '.join(missing)}"]

    # Document strength
    doc_count = sum([
        1 if docs.get("kyc") else 0,
        1 if docs.get("income_proof") else 0,
        1 if docs.get("bank_statement") else 0,
        1 if docs.get("loan_document") else 0
    ])

    if doc_count < 3:
        reasons.append("Weak document support")
        risk_score += 20

    # =====================================================
    # 🔹 3. HARD REJECTION RULES
    # =====================================================
    if claim > loan:
        return "Reject", ["Claim exceeds loan amount"]

    # Unrealistic EMI check
    if tenure > 0:
        expected_emi = loan / tenure
        if emi > 0 and emi < expected_emi * 0.2:
            return "Reject", ["EMI unrealistically low"]

    # =====================================================
    # 🔹 4. EMI AFFORDABILITY (FOIR)
    # =====================================================
    emi_ratio = emi / income if income > 0 else 0

    if emi_ratio > 0.7:
        reasons.append("EMI exceeds 70% of income")
        risk_score += 40
    elif emi_ratio > 0.5:
        reasons.append("EMI high relative to income")
        risk_score += 20

    # =====================================================
    # 🔹 5. LOAN vs INCOME (FIXED ✅)
    # =====================================================
    annual_income = income * 12
    loan_ratio = loan / annual_income

    if loan_ratio > 8:
        reasons.append("Loan extremely high vs income")
        risk_score += 40

    elif loan_ratio > 5:
        reasons.append("Loan high vs income")
        risk_score += 20

    elif loan_ratio > 3:
        reasons.append("Loan moderate vs income")

    # =====================================================
    # 🔹 6. CLAIM CONSISTENCY
    # =====================================================
    claim_ratio = claim / loan if loan > 0 else 0

    if claim_ratio > 0.95:
        reasons.append("Claim close to full loan amount")
        decision = "Needs Review"

    elif claim_ratio > 0.8:
        reasons.append("High claim relative to loan")
        risk_score += 20

    elif claim_ratio < 0.1:
        reasons.append("Low claim amount (normal case)")

    # =====================================================
    # 🔹 7. POLICY TIMING
    # =====================================================
    if policy_age < 1 and claim_ratio > 0.5:
        reasons.append("Early claim after policy start")
        risk_score += 30

    # =====================================================
    # 🔹 8. CLAIM HISTORY
    # =====================================================
    if history >= 3:
        reasons.append("Multiple previous claims")
        risk_score += 25

    # =====================================================
    # 🔹 9. EMI CONSISTENCY (TENURE BASED)
    # =====================================================
    if tenure > 0 and emi > 0:
        expected_emi = loan / tenure

        if emi < expected_emi * 0.5:
            reasons.append("EMI lower than expected")
            risk_score += 20

        elif emi > expected_emi * 1.5:
            reasons.append("EMI higher than expected")
            risk_score += 10

    # =====================================================
    # 🔹 FINAL DECISION (SAFE OVERRIDE)
    # =====================================================
    if decision != "Needs Review":
        if risk_score >= 80:
            decision = "Reject"
        elif risk_score >= 40:
            decision = "Needs Review"
        else:
            decision = "Approve"

    if not reasons:
        reasons.append("All financial checks passed")

    return decision, reasons