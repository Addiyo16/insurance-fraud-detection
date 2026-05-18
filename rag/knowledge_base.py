KNOWLEDGE_BASE = [
    {
        "id": "health_required_documents",
        "domain": "Health",
        "title": "Health claim document completeness",
        "text": (
            "Health claims should be assessed only after the final bill, medical report, "
            "and customer identity documents are available. Missing mandatory documents "
            "should normally move the claim to manual review instead of automatic approval."
        ),
    },
    {
        "id": "health_billing_consistency",
        "domain": "Health",
        "title": "Health billing consistency",
        "text": (
            "Hospital charges should be consistent with diagnosis severity, admission type, "
            "length of stay, ICU usage, medicine proportion, and whether the hospital is in "
            "network. Very high per-day cost or ICU use for minor illness is a strong anomaly."
        ),
    },
    {
        "id": "vehicle_idv_limit",
        "domain": "Vehicle",
        "title": "Vehicle IDV and loss consistency",
        "text": (
            "Vehicle repair claims should not exceed the insured declared value. The damage "
            "amount should be consistent with accident severity, vehicle type, report delay, "
            "supporting images, police report, and registration certificate."
        ),
    },
    {
        "id": "vehicle_low_idv_minor_loss",
        "domain": "Vehicle",
        "title": "Low-IDV vehicle minor accident review",
        "text": (
            "For low-IDV vehicles, a minor accident with repair cost above a meaningful "
            "share of IDV should be investigated because the economics can resemble an "
            "inflated repair estimate or constructive total-loss attempt."
        ),
    },
    {
        "id": "document_fact_matching",
        "domain": "All",
        "title": "Document-to-claim fact matching",
        "text": (
            "Claim form values should match the supporting documents. Differences in vehicle "
            "number, IDV, bill amount, diagnosis, cause of death, income, loan amount, EMI, "
            "or policy details should trigger review or rejection depending on materiality."
        ),
    },
    {
        "id": "vehicle_document_evidence",
        "domain": "Vehicle",
        "title": "Vehicle evidence requirements",
        "text": (
            "Vehicle claim review should verify registration certificate, police report where "
            "required, and accident images. Weak evidence or late reporting increases the need "
            "for investigation."
        ),
    },
    {
        "id": "life_contestability",
        "domain": "Life",
        "title": "Life policy early-claim scrutiny",
        "text": (
            "Life claims made soon after policy inception require enhanced scrutiny. Review "
            "should verify policy status, sum assured, death certificate, medical evidence, "
            "cause of death, and police documentation for accidental death."
        ),
    },
    {
        "id": "life_claim_amount",
        "domain": "Life",
        "title": "Life claim amount consistency",
        "text": (
            "A full sum-assured claim can be normal in life insurance, but it becomes higher "
            "risk when combined with very early policy age, missing medical records, inactive "
            "policy status, or inconsistent cause-of-death evidence."
        ),
    },
    {
        "id": "financial_affordability",
        "domain": "Financial",
        "title": "Financial claim affordability checks",
        "text": (
            "Credit and financial protection claims should compare loan amount, income, EMI, "
            "tenure, claim amount, bank statements, income proof, KYC, and loan documents. "
            "Extreme debt-to-income or EMI-to-income ratios are strong risk indicators."
        ),
    },
    {
        "id": "financial_loan_consistency",
        "domain": "Financial",
        "title": "Financial loan consistency",
        "text": (
            "A claim should not exceed the outstanding or covered loan amount. EMI should be "
            "plausible for the loan and tenure, and early high-value claims should receive "
            "manual investigation."
        ),
    },
    {
        "id": "cross_domain_decisioning",
        "domain": "All",
        "title": "Decisioning governance",
        "text": (
            "Automated fraud systems should combine hard rules, risk scoring, document checks, "
            "claim history, and human review thresholds. High-risk decisions should explain the "
            "specific evidence used and avoid presenting probabilistic scores as legal proof."
        ),
    },
]
