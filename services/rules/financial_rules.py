from services.rules.evidence import (
    add_amount_mismatch,
    final_decision,
    missing_document_facts,
    missing_facts_reason,
    number,
)


def run(data):
    reasons = []
    risk_score = 0

    financial = data.get("financial", {})
    policy = data.get("policy", {})
    docs = data.get("documents", {})
    document_info = data.get("document_info", {})
    history = number(data.get("history", 0))

    income = number(financial.get("income"))
    loan = number(financial.get("loan_amount"))
    claim = number(financial.get("claim_amount"))
    emi = number(policy.get("emi_amount"))
    tenure = number(policy.get("tenure_months"))
    policy_age = number(policy.get("age_months", 12))

    if income <= 0 or loan <= 0:
        return "Needs Review", ["Income or loan amount is missing or invalid"], 55
    if claim <= 0:
        return "Needs Review", ["Claim amount is missing or invalid"], 50

    required_docs = ["kyc", "income_proof", "bank_statement", "loan_document"]
    missing = [doc for doc in required_docs if not docs.get(doc)]
    if missing:
        return "Needs Review", [f"Missing financial claim documents: {', '.join(missing)}"], 55

    missing_facts = missing_document_facts(document_info, ["income", "loan_amount", "emi_amount"])
    if missing_facts:
        return "Needs Review", [missing_facts_reason("Financial", missing_facts)], 70

    income_mismatch = add_amount_mismatch(
        reasons,
        "income",
        income,
        document_info.get("income"),
        tolerance=0.08,
        risk_points=1,
    )
    if income_mismatch:
        return "Reject", ["Invalid claim details: income does not match income proof or bank statement"], 90

    loan_mismatch = add_amount_mismatch(
        reasons,
        "loan amount",
        loan,
        document_info.get("loan_amount"),
        tolerance=0.03,
        risk_points=1,
    )
    if loan_mismatch:
        return "Reject", ["Invalid claim details: loan amount does not match loan document"], 92

    emi_mismatch = add_amount_mismatch(
        reasons,
        "EMI",
        emi,
        document_info.get("emi_amount"),
        tolerance=0.08,
        risk_points=1,
    )
    if emi_mismatch:
        return "Reject", ["Invalid claim details: EMI does not match loan or bank statement document"], 88

    if claim > loan:
        return "Reject", ["Claim amount exceeds the covered loan amount"], 98

    if tenure > 0 and emi > 0:
        expected_emi = loan / tenure
        if emi < expected_emi * 0.2:
            return "Reject", ["Declared EMI is unrealistically low for the loan amount and tenure"], 92
        if emi < expected_emi * 0.5:
            reasons.append("EMI is lower than expected for loan amount and tenure")
            risk_score += 20
        elif emi > expected_emi * 1.5:
            reasons.append("EMI is higher than expected for loan amount and tenure")
            risk_score += 10

    emi_ratio = emi / income if income > 0 else 0
    if emi_ratio > 0.70:
        reasons.append("EMI exceeds 70% of monthly income")
        risk_score += 40
    elif emi_ratio > 0.50:
        reasons.append("EMI is high relative to monthly income")
        risk_score += 20

    loan_to_annual_income = loan / (income * 12)
    if loan_to_annual_income > 8:
        reasons.append("Loan amount is extremely high compared with annual income")
        risk_score += 40
    elif loan_to_annual_income > 5:
        reasons.append("Loan amount is high compared with annual income")
        risk_score += 20

    claim_ratio = claim / loan
    if claim_ratio > 0.95:
        reasons.append("Claim is close to the full loan amount")
        risk_score += 25
    elif claim_ratio > 0.80:
        reasons.append("Claim is high relative to loan amount")
        risk_score += 20

    if policy_age < 1 and claim_ratio > 0.5:
        reasons.append("High claim occurred within the first policy month")
        risk_score += 30
    if history >= 3:
        reasons.append("Multiple previous financial protection claims are linked to the customer")
        risk_score += 25

    return final_decision(
        risk_score,
        reasons,
        "Financial claim passed document, affordability, loan, EMI, timing, and history checks",
    )
