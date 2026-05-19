import re

from ocr.extractor import extract_documents_text


AMOUNT = r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)"


def _amount(value):
    if not value:
        return None
    try:
        cleaned = re.sub(r"[^0-9.]", "", str(value))
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _first(patterns, text, flags=re.IGNORECASE):
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()
    return None


def _label_value(label, text):
    pattern = rf"(?im)^\s*{re.escape(label)}\s*$\s*^\s*(.+?)\s*$"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return None


def _label_values(label, text):
    pattern = rf"(?im)^\s*{re.escape(label)}\s*$\s*^\s*(.+?)\s*$"
    return [match.strip() for match in re.findall(pattern, text) if match.strip()]


def _first_label(labels, text):
    for label in labels:
        value = _label_value(label, text)
        if value:
            return value
    return None


def _all_label_values(labels, text):
    values = []
    for label in labels:
        values.extend(_label_values(label, text))
    return values


def _first_label_amount(labels, text):
    return _amount(_first_label(labels, text))


def _first_amount(patterns, text):
    value = _first(patterns, text)
    return _amount(value)


def parse_document_info(domain, text):
    text = text or ""
    if domain == "Health":
        return {
            "patient_names": _all_label_values(["Patient Name"], text),
            "policyholder_name": _first_label(["Policyholder Name"], text),
            "hospital_name": _first_label(["Hospital", "Hospital Name"], text),
            "diagnosis": _first_label(["Diagnosis", "Treatment"], text)
            or _first([r"diagnosis\s*[:\-]\s*([A-Za-z0-9 /,.-]+)"], text),
            "treatment": _first_label(["Treatment", "Recommendation", "Procedure"], text),
            "total_bill": _first_label_amount(
                ["Final Amount", "Total Amount", "Total Bill", "Final Bill", "Net Payable", "Amount Payable"],
                text,
            )
            or _first_amount(
                    [
                        rf"(?:total bill|final bill|final amount|total amount|gross amount|net payable)\s*[:\-]?\s*(?:rs\.?|inr|₹|\?)?\s*{AMOUNT}",
                        rf"(?:amount payable)\s*[:\-]?\s*(?:rs\.?|inr|₹|\?)?\s*{AMOUNT}",
                    ],
                    text,
            ),
            "days": _first_label_amount(["Hospitalization Days", "Length of Stay", "No. of Days"], text)
            or _first_amount([r"(?:hospitalization days|length of stay|no\.? of days)\s*[:\-]?\s*([0-9]+)"], text),
        }

    if domain == "Vehicle":
        return {
            "vehicle_number": _first_label(["Vehicle No", "Vehicle Number", "Registration No", "Regn. No", "RC No"], text)
            or _first(
                [
                    r"(?:vehicle no|registration no|regn\.? no|rc no)\s*[:\-]\s*([A-Z0-9 -]+)",
                    r"\b([A-Z]{2}\s?[0-9]{1,2}\s?[A-Z]{1,3}\s?[0-9]{4})\b",
                ],
                text,
            ),
            "idv": _first_label_amount(["IDV", "Insured Declared Value"], text)
            or _first_amount([rf"(?:idv|insured declared value)\s*[:\-]?\s*(?:rs\.?|inr|₹|\?)?\s*{AMOUNT}"], text),
            "estimated_cost": _first_label_amount(["Repair Estimate", "Estimated Repair", "Estimate Amount", "Net Estimate", "Total Repair Cost"], text)
            or _first_amount(
                [
                    rf"(?:repair estimate|estimated repair|estimate amount|net estimate)\s*[:\-]?\s*(?:rs\.?|inr|₹|\?)?\s*{AMOUNT}",
                    rf"(?:total repair cost)\s*[:\-]?\s*(?:rs\.?|inr|₹|\?)?\s*{AMOUNT}",
                ],
                text,
            ),
            "accident_type": _first_label(["Accident Severity", "Loss Severity", "Accident Type"], text)
            or _first([r"(?:accident severity|loss severity|accident type)\s*[:\-]\s*(minor|major)"], text),
        }

    if domain == "Life":
        return {
            "cause": _first_label(["Cause of Death", "Death Cause"], text)
            or _first([r"(?:cause of death|death cause)\s*[:\-]\s*([A-Za-z ]+)"], text),
            "sum_assured": _first_label_amount(["Sum Assured", "Sum Insured", "Coverage Amount"], text)
            or _first_amount([rf"(?:sum assured|sum insured|coverage amount)\s*[:\-]?\s*(?:rs\.?|inr|₹|\?)?\s*{AMOUNT}"], text),
        }

    return {
        "income": _first_label_amount(["Monthly Income", "Net Salary", "Salary"], text)
        or _first_amount([rf"(?:monthly income|net salary|salary)\s*[:\-]?\s*(?:rs\.?|inr|₹|\?)?\s*{AMOUNT}"], text),
        "loan_amount": _first_label_amount(["Loan Amount", "Principal Amount", "Sanctioned Amount"], text)
        or _first_amount([rf"(?:loan amount|principal amount|sanctioned amount)\s*[:\-]?\s*(?:rs\.?|inr|₹|\?)?\s*{AMOUNT}"], text),
        "emi_amount": _first_label_amount(["EMI", "Monthly Installment", "Instalment"], text)
        or _first_amount([rf"(?:emi|monthly installment|instalment)\s*[:\-]?\s*(?:rs\.?|inr|₹|\?)?\s*{AMOUNT}"], text),
    }


def extract_document_info(domain, documents):
    text = extract_documents_text(documents)
    info = parse_document_info(domain, text)
    return {key: value for key, value in info.items() if value not in (None, "")}, text
