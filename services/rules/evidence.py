def normalize_text(value):
    return " ".join(str(value or "").strip().lower().split())


def normalize_vehicle_number(value):
    return "".join(ch for ch in normalize_text(value).upper() if ch.isalnum())


def number(value, default=0):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


def near(left, right, tolerance=0.05):
    left = number(left)
    right = number(right)
    if left == 0 and right == 0:
        return True
    baseline = max(abs(left), abs(right), 1)
    return abs(left - right) / baseline <= tolerance


def add_text_mismatch(reasons, label, claim_value, document_value, risk_points=25):
    if document_value in (None, ""):
        return 0
    if normalize_text(claim_value) != normalize_text(document_value):
        reasons.append(
            f"{label} mismatch: claim says '{claim_value}', document says '{document_value}'"
        )
        return risk_points
    return 0


def add_amount_mismatch(reasons, label, claim_value, document_value, tolerance=0.05, risk_points=30):
    if document_value in (None, "", 0, 0.0):
        return 0
    if not near(claim_value, document_value, tolerance=tolerance):
        reasons.append(
            f"{label} mismatch: claim amount {claim_value} differs from document amount {document_value}"
        )
        return risk_points
    return 0


def missing_document_facts(document_info, required_fields):
    return [
        field
        for field in required_fields
        if document_info.get(field) in (None, "", 0, 0.0)
    ]


def missing_facts_reason(domain, missing):
    return (
        f"Invalid or unverifiable {domain.lower()} document details: could not extract "
        f"{', '.join(missing)} from uploaded documents. Do not approve until document facts are readable and verified."
    )


def score_band(value, bands):
    """Return points for a value using ordered threshold bands.

    Example: score_band(0.6, [(0.3, 15), (0.5, 35), (0.75, 70)])
    returns 35.
    """
    points = 0
    for threshold, band_points in bands:
        if value >= threshold:
            points = band_points
    return points


def final_decision(risk_score, reasons, approve_reason, reject_at=85, review_at=35):
    if risk_score >= reject_at:
        decision = "Reject"
    elif risk_score >= review_at:
        decision = "Needs Review"
    else:
        decision = "Approve"

    if not reasons:
        reasons.append(approve_reason)

    return decision, reasons, round(min(max(risk_score, 0), 100), 2)
