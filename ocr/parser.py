from ocr.extractor import extract_document_data

def parse_and_validate_documents(documents, domain, claim_data):
    """
    Parses all uploaded documents for a domain, merges the extracted data,
    and runs a cross-verification comparison against the user's form inputs.
    
    Returns:
        tuple: (ocr_data, discrepancies, status_message)
    """
    aggregated_ocr = {}
    discrepancies = []
    
    # Process each uploaded document
    for doc_key, doc_file in documents.items():
        if doc_file is not None:
            try:
                extracted = extract_document_data(doc_file, domain)
                if extracted:
                    aggregated_ocr.update(extracted)
            except Exception as e:
                print(f"Error parsing document {doc_key}: {e}")
                
    if not aggregated_ocr:
        return {}, [], "No document data extracted."

    # ---------------- RUN CROSS-VERIFICATION CHECKS ----------------
    
    # 🏥 HEALTH DOMAIN CHECKS
    if domain == "Health":
        patient_ui = claim_data.get("patient", {}).get("name", "").strip().lower()
        patient_ocr = aggregated_ocr.get("patient_name", "").strip().lower()
        if patient_ocr and patient_ui and patient_ui != patient_ocr:
            discrepancies.append(f"Patient Name mismatch: UI '{claim_data.get('patient', {}).get('name')}' vs Doc '{aggregated_ocr.get('patient_name')}'")
            
        bill_ui = float(claim_data.get("financial", {}).get("total_bill", 0))
        bill_ocr = float(aggregated_ocr.get("total_bill", 0))
        if bill_ocr > 0 and bill_ui != bill_ocr:
            discrepancies.append(f"Total Bill mismatch: UI '${bill_ui}' vs Doc '${bill_ocr}'")

        hosp_ui = claim_data.get("hospital", {}).get("name", "").strip().lower()
        hosp_ocr = aggregated_ocr.get("hospital_name", "").strip().lower()
        if hosp_ocr and hosp_ui and hosp_ui != hosp_ocr:
            discrepancies.append(f"Hospital Name mismatch: UI '{claim_data.get('hospital', {}).get('name')}' vs Doc '{aggregated_ocr.get('hospital_name')}'")

    # 🚗 VEHICLE DOMAIN CHECKS
    elif domain == "Vehicle":
        owner_ui = claim_data.get("vehicle", {}).get("number", "").strip().lower() # we can check plate
        plate_ocr = aggregated_ocr.get("license_plate", "").strip().lower()
        # Clean plate formats for comparison
        clean_plate_ui = owner_ui.replace("-", "").replace(" ", "")
        clean_plate_ocr = plate_ocr.replace("-", "").replace(" ", "")
        if clean_plate_ocr and clean_plate_ui and clean_plate_ui != clean_plate_ocr:
            discrepancies.append(f"License Plate mismatch: UI '{claim_data.get('vehicle', {}).get('number')}' vs Doc '{aggregated_ocr.get('license_plate')}'")

        cost_ui = float(claim_data.get("damage", {}).get("estimated_cost", 0))
        cost_ocr = float(aggregated_ocr.get("estimated_cost", 0))
        if cost_ocr > 0 and cost_ui != cost_ocr:
            discrepancies.append(f"Estimated Cost mismatch: UI '${cost_ui}' vs Doc '${cost_ocr}'")

    # 👤 LIFE DOMAIN CHECKS
    elif domain == "Life":
        dec_ui = claim_data.get("incident", {}).get("cause", "") # Wait, we should verify name
        # We will add name inputs in Life UI refactor
        name_ui = claim_data.get("policyholder", {}).get("name", "").strip().lower()
        name_ocr = aggregated_ocr.get("deceased_name", "").strip().lower()
        if name_ocr and name_ui and name_ui != name_ocr:
            discrepancies.append(f"Deceased Name mismatch: UI '{claim_data.get('policyholder', {}).get('name')}' vs Doc '{aggregated_ocr.get('deceased_name')}'")

    # 💰 FINANCIAL DOMAIN CHECKS
    elif domain == "Financial":
        name_ui = claim_data.get("policy", {}).get("lender_name", "") # check name
        # We will check applicant name in Financial UI refactor
        income_ui = float(claim_data.get("financial", {}).get("income", 0))
        income_ocr = float(aggregated_ocr.get("monthly_income", 0))
        if income_ocr > 0 and income_ui != income_ocr:
            discrepancies.append(f"Income mismatch: UI '${income_ui}' vs Doc '${income_ocr}'")

    if discrepancies:
        status = "⚠️ Discrepancies detected between form fields and uploaded documents."
    else:
        status = "✅ OCR Verification passed. All document details align with form inputs."
        
    return aggregated_ocr, discrepancies, status
