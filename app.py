import sys
import os
import importlib
import streamlit as st
import pandas as pd

# -------- PATH FIX --------
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# -------- PIPELINE --------
pipeline = importlib.import_module("services.pipeline")
run_pipeline = pipeline.run_pipeline

# -------- CONFIG --------
st.set_page_config(page_title="Insurance AI System", layout="wide") 

st.title("🛡️ Insurance Claim Intelligence System")
st.caption("AI-powered fraud detection system")

# =====================================================
# 🔹 SIDEBAR (ONLY DOMAIN)
# =====================================================
st.sidebar.title("🧭 Insurance Domains")

domain = st.sidebar.radio(
    "Select Domain",
    ["🏥 Health", "🚗 Vehicle", "👤 Life", "💰 Financial"]
)

domain = domain.split(" ")[1]

# -------- SESSION --------
if "history" not in st.session_state:
    st.session_state.history = []

# =====================================================
# 🔹 HEALTH UI
# =====================================================
import streamlit as st
from ocr.parser import extract_document_info

def attach_extracted_document_info(domain, data):
    info, text = extract_document_info(domain, data.get("documents", {}))
    data["document_info"] = info
    data["document_text"] = text

    with st.expander("Extracted document facts", expanded=False):
        if info:
            st.json(info)
        else:
            st.info("No structured facts were extracted. Use text-based PDFs for best local extraction.")

    return data

def health_ui():
    data = {}

    tabs = st.tabs([
        "👤 Policyholder",
        "👥 Patient",
        "🏥 Hospital",
        "📅 Admission",
        "💰 Financial",
        "📄 Documents"
    ])

    # ---------------- POLICYHOLDER ----------------
    with tabs[0]:
        data["policyholder"] = {
            "name": st.text_input("Policyholder Name"),
            "policy_no": st.text_input("Policy Number")
        }

    # ---------------- PATIENT ----------------
    with tabs[1]:
        data["patient"] = {
            "name": st.text_input("Patient Name"),
            "age": st.number_input("Age", 0, 120),
            "gender": st.selectbox("Gender", ["Male", "Female", "Other"])
        }

    # ---------------- HOSPITAL ----------------
    with tabs[2]:
        data["hospital"] = {
            "name": st.text_input("Hospital Name"),
            "network": st.checkbox("Network Hospital", True),
            "diagnosis": st.text_input("Diagnosis")
        }

    # ---------------- ADMISSION ----------------
    with tabs[3]:
        data["admission"] = {
            "type": st.selectbox("Admission Type", ["Planned", "Emergency"]),
            "days": st.number_input("Hospitalization Days", 0)
        }

    # ---------------- FINANCIAL ----------------
    with tabs[4]:
        data["financial"] = {
            "total_bill": st.number_input("Total Bill", 0),
            "icu": st.number_input("ICU Charges", 0),
            "medicine": st.number_input("Medicine Cost", 0)
        }

    # ---------------- DOCUMENTS (FIXED) ----------------
    with tabs[5]:
        st.subheader("📄 Upload Required Documents")

        # Initialize session storage
        if "health_docs" not in st.session_state:
            st.session_state.health_docs = {
                "final_bill": None,
                "medical_report": None,
                "kyc": None
            }

        fb = st.file_uploader("Upload Final Bill (PDF)", type=["pdf"], key="fb")
        mr = st.file_uploader("Upload Medical Report", type=["pdf", "jpg", "png"], key="mr")
        kyc = st.file_uploader("Upload KYC Document", type=["pdf", "jpg", "png"], key="kyc")

        # Store permanently
        if fb is not None:
            st.session_state.health_docs["final_bill"] = fb
        if mr is not None:
            st.session_state.health_docs["medical_report"] = mr
        if kyc is not None:
            st.session_state.health_docs["kyc"] = kyc

        # Show upload status
        st.write({
            "final_bill": st.session_state.health_docs["final_bill"] is not None,
            "medical_report": st.session_state.health_docs["medical_report"] is not None,
            "kyc": st.session_state.health_docs["kyc"] is not None
        })

        # Assign to data
        data["documents"] = st.session_state.health_docs
        attach_extracted_document_info("Health", data)

    return data

# =====================================================
# 🔹 VEHICLE UI
# =====================================================
def vehicle_ui():
    data = {}

    tabs = st.tabs([
        "🚗 Vehicle",
        "📍 Incident",
        "💰 Damage",
        "📄 Documents"
    ])

    # ---------------- VEHICLE ----------------
    with tabs[0]:
        data["vehicle"] = {
            "number": st.text_input("Vehicle Number", key="vehicle_number"),
            "type": st.selectbox("Type", ["Car", "Bike", "Truck"], key="vehicle_type"),
            "idv": st.number_input("Insured Declared Value (IDV)", 0, key="vehicle_idv")
        }

    # ---------------- INCIDENT (UPDATED) ----------------
    with tabs[1]:
        data["incident"] = {
        "type": st.selectbox("Accident Type", ["Minor", "Major"], key="incident_type"),
        "location": st.text_input("Location", key="incident_location")
    }

    # ---------------- DAMAGE ----------------
    with tabs[2]:
        data["damage"] = {
            "estimated_cost": st.number_input("Damage Cost", 0, key="damage_cost")
        }

    # ---------------- DOCUMENTS ----------------
    with tabs[3]:
        data["documents"] = {
            "rc": st.file_uploader("RC Document", key="doc_rc"),
            "police": st.file_uploader("Police Report", key="doc_police"),
            "images": st.file_uploader("Accident Images", key="doc_images")
        }
        attach_extracted_document_info("Vehicle", data)

    return data

# =====================================================
# 🔹 LIFE UI
# =====================================================
def life_ui():
    data = {}

    tabs = st.tabs([
        "📜 Policy",
        "⚰️ Incident",
        "💰 Financial",
        "📄 Documents"
    ])

    with tabs[0]:
        data["policy"] = {
            "age_years": st.number_input("Policy Age (years)", 0.0),
            "sum_assured": st.number_input("Sum Assured", 0),
            "active": st.checkbox("Policy Active", True),
            "type": st.selectbox("Policy Type", ["Term", "Whole Life"])
        }

    with tabs[1]:
        data["incident"] = {
            "cause": st.selectbox("Cause of Death", ["Natural", "Illness", "Accident"]),
            "hospitalized": st.checkbox("Hospitalization Record Available", False),
            "date": st.date_input("Date of Death")
        }

    with tabs[2]:
        data["financial"] = {
            "claim_amount": st.number_input("Claim Amount", 0)
        }

    with tabs[3]:
        data["documents"] = {
            "death_certificate": st.file_uploader("Death Certificate"),
            "medical_report": st.file_uploader("Medical Report"),
            "police_report": st.file_uploader("Police Report")
        }
        attach_extracted_document_info("Life", data)

    return data

# =====================================================
# 🔹 FINANCIAL UI
# =====================================================
def financial_ui():
    data = {}

    tabs = st.tabs([
        "🏢 Loan Details",
        "💰 Financial",
        "📄 Documents"
    ])

    with tabs[0]:
        data["policy"] = {
            "lender_name": st.text_input("Lender / Company Name"),
            "loan_id": st.text_input("Loan ID"),
            "loan_type": st.selectbox("Loan Type", ["Personal", "Home", "Auto"]),
            "tenure_months": st.number_input("Tenure (months)", 0),
            "emi_amount": st.number_input("EMI Amount", 0)
        }

    with tabs[1]:
        data["financial"] = {
            "income": st.number_input("Monthly Income", 0),
            "loan_amount": st.number_input("Loan Amount", 0),
            "claim_amount": st.number_input("Claim Amount", 0)
        }

    with tabs[2]:
        data["documents"] = {
            "kyc": st.file_uploader("KYC Document"),
            "income_proof": st.file_uploader("Income Proof"),
            "bank_statement": st.file_uploader("Bank Statement"),
            "loan_document": st.file_uploader("Loan Agreement")
        }
        attach_extracted_document_info("Financial", data)

    return data

# =====================================================
# 🔹 LOAD DOMAIN
# =====================================================
if domain == "Health":
    claim_data = health_ui()

elif domain == "Vehicle":
    claim_data = vehicle_ui()

elif domain == "Life":
    claim_data = life_ui()

else:
    claim_data = financial_ui()

# =====================================================
# 🔹 ANALYZE (UPDATED)
# =====================================================
# =====================================================
# 🔹 ANALYZE (FIXED)
# =====================================================
st.markdown("---")

documents = claim_data.get("documents", {})

# ---------------- DOMAIN-WISE DOCUMENT CHECK ----------------

if domain == "Health":

    # 🔥 FIX: use session_state (correct source)
    documents = st.session_state.get("health_docs", {})
    claim_data["documents"] = documents

    docs_uploaded = all([
        documents.get("final_bill") is not None,
        documents.get("medical_report") is not None,
        documents.get("kyc") is not None
    ])

elif domain == "Vehicle":
    docs_uploaded = all([
        documents.get("rc"),
        documents.get("police"),
        documents.get("images")
    ])

elif domain == "Life":
    docs_uploaded = all([
        documents.get("death_certificate")
    ])

elif domain == "Financial":
    docs_uploaded = all([
        documents.get("kyc"),
        documents.get("income_proof"),
        documents.get("bank_statement"),
        documents.get("loan_document")
    ])

else:
    docs_uploaded = True

# ---------------- WARNING ----------------
if not docs_uploaded:
    st.warning("⚠️ Please upload all required documents before analysis")

# ---------------- BUTTON ----------------
if st.button("🔍 Analyze Claim", use_container_width=True, disabled=not docs_uploaded):

    result = run_pipeline(domain, claim_data)

    st.markdown("## 📊 Claim Decision")

    col1, col2, col3 = st.columns(3)

    col1.metric("Decision", result["decision"])
    col2.metric("Fraud Risk", f"{result['fraud_score']}%")
    col3.metric("Domain", domain)

    st.progress(int(result["fraud_score"]))

    if result["decision"] == "Reject":
        st.error("❌ High Fraud Risk")

    elif result["decision"] == "Needs Review":
        st.warning("⚠️ Needs Investigation")

    else:
        st.success("✅ Claim Approved")

    st.markdown("### 🧠 Explanation")
    st.write(result["explanation"])

# =====================================================
# 🔹 ANALYTICS
# =====================================================
if st.session_state.history:

    st.markdown("---")
    st.header("📈 Analytics")

    df = pd.DataFrame(st.session_state.history)

    col1, col2 = st.columns(2)

    col1.bar_chart(df["domain"].value_counts())
    col2.bar_chart(df.groupby("domain")["fraud"].mean())

