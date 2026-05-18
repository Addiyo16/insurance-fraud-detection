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


def final_decision(risk_score, reasons, approve_reason):
    if risk_score >= 85:
        decision = "Reject"
    elif risk_score >= 35:
        decision = "Needs Review"
    else:
        decision = "Approve"

    if not reasons:
        reasons.append(approve_reason)

    return decision, reasons
