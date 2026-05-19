import re

from ocr.extractor import extract_documents_text


AMOUNT = r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)"


def _amount(value):
    if not value:
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def _first(patterns, text, flags=re.IGNORECASE):
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()
    return None


def _first_amount(patterns, text):
    value = _first(patterns, text)
    return _amount(value)


def parse_document_info(domain, text):
    text = text or ""
    if domain == "Health":
        return {
            "diagnosis": _first([r"diagnosis\s*[:\-]\s*([A-Za-z0-9 /,.-]+)"], text),
            "total_bill": _first_amount(
                [
                    rf"(?:total bill|final bill|gross amount|net payable)\s*[:\-]?\s*(?:rs\.?|inr)?\s*{AMOUNT}",
                    rf"(?:amount payable)\s*[:\-]?\s*(?:rs\.?|inr)?\s*{AMOUNT}",
                ],
                text,
            ),
            "days": _first_amount([r"(?:hospitalization days|length of stay|no\.? of days)\s*[:\-]?\s*([0-9]+)"], text),
        }

    if domain == "Vehicle":
        return {
            "vehicle_number": _first(
                [
                    r"(?:vehicle no|registration no|regn\.? no|rc no)\s*[:\-]\s*([A-Z0-9 -]+)",
                    r"\b([A-Z]{2}\s?[0-9]{1,2}\s?[A-Z]{1,3}\s?[0-9]{4})\b",
                ],
                text,
            ),
            "idv": _first_amount([rf"(?:idv|insured declared value)\s*[:\-]?\s*(?:rs\.?|inr)?\s*{AMOUNT}"], text),
            "estimated_cost": _first_amount(
                [
                    rf"(?:repair estimate|estimated repair|estimate amount|net estimate)\s*[:\-]?\s*(?:rs\.?|inr)?\s*{AMOUNT}",
                    rf"(?:total repair cost)\s*[:\-]?\s*(?:rs\.?|inr)?\s*{AMOUNT}",
                ],
                text,
            ),
            "accident_type": _first([r"(?:accident severity|loss severity|accident type)\s*[:\-]\s*(minor|major)"], text),
        }

    if domain == "Life":
        return {
            "cause": _first([r"(?:cause of death|death cause)\s*[:\-]\s*([A-Za-z ]+)"], text),
            "sum_assured": _first_amount([rf"(?:sum assured|sum insured|coverage amount)\s*[:\-]?\s*(?:rs\.?|inr)?\s*{AMOUNT}"], text),
        }

    return {
        "income": _first_amount([rf"(?:monthly income|net salary|salary)\s*[:\-]?\s*(?:rs\.?|inr)?\s*{AMOUNT}"], text),
        "loan_amount": _first_amount([rf"(?:loan amount|principal amount|sanctioned amount)\s*[:\-]?\s*(?:rs\.?|inr)?\s*{AMOUNT}"], text),
        "emi_amount": _first_amount([rf"(?:emi|monthly installment|instalment)\s*[:\-]?\s*(?:rs\.?|inr)?\s*{AMOUNT}"], text),
    }


def extract_document_info(domain, documents):
    text = extract_documents_text(documents)
    info = parse_document_info(domain, text)
    return {key: value for key, value in info.items() if value not in (None, "")}, text
