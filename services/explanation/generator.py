import os
import google.generativeai as genai
from rag.retriever import retrieve_policy_context

# Configure API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_explanation(domain, claim_data, rule_decision, rule_reasons, ml_score, ocr_discrepancies, final_decision, final_score):
    """
    RAG-powered Explainer: Retrieves relevant policy clauses and prompts Gemini
    to synthesize a formal Claims Audit Report detailing the approval or denial reasoning.
    """
    # 1. Retrieve Policy Context
    # Extract keywords from rules reasons
    keywords = []
    for reason in rule_reasons:
        for word in ["suicide", "blacklist", "exceed", "limit", "stolen", "doctor", "hospital", "income"]:
            if word in reason.lower() and word not in keywords:
                keywords.append(word)

    policy_context = retrieve_policy_context(domain, keywords)

    # 2. Format details for the prompt
    reasons_text = "\n- ".join(rule_reasons) if rule_reasons else "No rule violations triggered."
    discrepancies_text = "\n- ".join(ocr_discrepancies) if ocr_discrepancies else "No document mismatches found."
    
    # Clean up claim data representation for the prompt
    clean_data = {}
    for k, v in claim_data.items():
        if k != "documents" and k != "ocr_data":  # Remove binary/large fields
            clean_data[k] = v

    # 3. Prompt Construction
    prompt = f"""
    You are an expert Insurance Claims Auditor. Write a formal executive 'Claims Audit Report' for a claim submitted in the '{domain}' domain.
    
    Use the following verified inputs to base your analysis:
    
    --- CLAIM DETAIL INPUTS ---
    {clean_data}
    
    --- VERIFICATION PIPELINE RESULTS ---
    - Rule Engine Decision: {rule_decision}
    - Triggered Violations:
      - {reasons_text}
    - Machine Learning Fraud Score: {ml_score}%
    - Document OCR Discrepancies:
      - {discrepancies_text}
    - Final Consolidated Score: {final_score}%
    - Final Decision: {final_decision}
    
    --- RETRIEVED POLICY CONTRACT CLAUSES ---
    {policy_context}
    
    --- REPORT REQUIREMENTS ---
    Structure your response as a professional document containing:
    1. 📋 EXECUTIVE SUMMARY: Clearly state the final decision (Approved, Rejected, or Held for Review) and the risk score.
    2. 🔍 CREDENTIAL & IDENTITY AUDIT: Detail database registry checks (Active policy, Owner name, Hospital/Doctor status, Vehicle registration, Death index, or Loan contracts) and document mismatches.
    3. 📜 POLICY CLAUSE CITATIONS: Cite the specific sections, subsections, or clauses from the retrieved policy contract that govern this decision (especially when denying or reviewing).
    4. 🧠 DETAILED RATIONALE: Provide a logical explanation of why the rules and ML flagged the claim (e.g. why split billing or owner mismatches indicate potential fraud).
    
    Use a professional, formal tone. Format with clear Markdown headers, bold text, and bullet points.
    """

    # 4. Generate Report (Gemini vs. Fallback Template)
    if not GEMINI_API_KEY:
        print("⚠️ Gemini API Key not found. Generating template-based Audit Report.")
        return _generate_local_template_report(domain, final_decision, final_score, rule_reasons, ocr_discrepancies, policy_context)

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Error calling Gemini API for explainer:", e)
        return _generate_local_template_report(domain, final_decision, final_score, rule_reasons, ocr_discrepancies, policy_context)

def _generate_local_template_report(domain, final_decision, final_score, rule_reasons, ocr_discrepancies, policy_context):
    """
    Fallback report generator when Gemini API is unavailable.
    """
    reasons_text = "\n- ".join(rule_reasons) if rule_reasons else "None"
    discrepancies_text = "\n- ".join(ocr_discrepancies) if ocr_discrepancies else "None"
    
    verdict_class = "❌ REJECTED" if final_decision == "Reject" else "⚠️ HELD FOR REVIEW" if final_decision == "Needs Review" else "✅ APPROVED"

    report = f"""
## 📋 CLAIMS AUDIT REPORT (LOCAL FALLBACK)

### 1. EXECUTIVE SUMMARY
* **Verdict:** {verdict_class}
* **Risk Probability:** {final_score}%
* **Domain:** {domain} Insurance

### 2. CREDENTIAL & IDENTITY AUDIT
* **Registry Status:** Database checks executed. Rule engine triggered anomalies:
  - {reasons_text}
* **Document Forgery Check:** OCR verification completed:
  - {discrepancies_text}

### 3. 📜 POLICY CLAUSE CITATIONS
The system reviewed the following relevant clauses from the retrieved contract:
```markdown
{policy_context}
```

### 4. 🧠 DETAILED RATIONALE
* **Rules Check:** The claim triggered policy violations that influenced the risk score.
* **ML Score:** Consolidated statistical modeling predicts a {final_score}% likelihood of anomaly based on historic fraud patterns.
* **Advisory:** Please configure the `GEMINI_API_KEY` environment variable in your environment to unlock the advanced, generative claims adjuster narrative.
"""
    return report.strip()