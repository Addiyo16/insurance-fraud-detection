import sys
import os
import warnings
import streamlit as st
import pandas as pd
import sqlite3

# Suppress google.generativeai deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# -------- PATH FIX --------
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from services.pipeline import run_pipeline

# -------- CONFIG & THEME --------
st.set_page_config(
    page_title="ShieldAI - Insurance Fraud & Intelligence System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Premium Aesthetics
st.markdown("""
<style>
    .main {
        background-color: #f9fbfd;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
        color: #e0e0e0;
    }
    .report-card {
        background-color: #0f172a;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        border-left: 6px solid #3b82f6;
        margin-bottom: 20px;
    }
    .report-card p, .report-card li, .report-card h1, .report-card h2, .report-card h3, .report-card h4, .report-card span, .report-card div, .report-card strong {
        color: #f1f5f9 !important;
    }
    .metric-card {
        background-color: #f0f4f8;
        padding: 16px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #d9e2ec;
    }
</style>
""", unsafe_allow_html=True)

# -------- DISTRIBUTED DATABASE VIEWER HELPER --------
DB_DIR = os.path.join(ROOT_DIR, "data")
DB_PATHS = {
    "insurance": os.path.join(DB_DIR, "insurance_company.db"),
    "medical": os.path.join(DB_DIR, "medical_registry.db"),
    "motor": os.path.join(DB_DIR, "motor_registry.db"),
    "death": os.path.join(DB_DIR, "death_registry.db"),
    "credit": os.path.join(DB_DIR, "credit_registry.db")
}

def query_db_table(query_or_table, db_key="insurance"):
    try:
        conn = sqlite3.connect(DB_PATHS[db_key])
        if query_or_table.strip().upper().startswith("SELECT"):
            sql = query_or_table
        else:
            sql = f"SELECT * FROM {query_or_table}"
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})

# =====================================================
# 🔹 SIDEBAR & NAVIGATION
# =====================================================
st.sidebar.image("https://img.icons8.com/color/96/shield.png", width=80)
st.sidebar.title("ShieldAI System")
st.sidebar.caption("AI-Powered Claims Audit & Fraud Detection")

role = st.sidebar.selectbox("🔑 Access Role", ["👤 Claimant (Customer)", "🕵️ Claims Auditor (Underwriter)"])

if role == "👤 Claimant (Customer)":
    menu_options = ["📋 Evaluate Claim Fraud", "✍️ Onboard New Policy"]
else:
    menu_options = ["🕵️ Registry Explorer & Analytics", "✍️ Onboard New Policy"]

sub_nav = st.sidebar.selectbox("🧭 Navigation Menu", menu_options)

domain_choice = st.sidebar.radio(
    "🧭 Select Insurance Domain",
    ["🏥 Health Insurance", "🚗 Vehicle Insurance", "👤 Life Insurance", "💰 Financial / Loan Protection"]
)

domain = domain_choice.split(" ")[1]

# Session state initialization for history
if "history" not in st.session_state:
    st.session_state.history = []

# =====================================================
# 👤 CLAIMANT DASHBOARD FORM BUILDER
# =====================================================
def render_claimant_form():
    st.header(f"📝 File a {domain} Claim")
    st.caption("Please provide policy registration details, claim metrics, and support documents.")
    
    claim_data = {}
    
    if domain == "Health":
        tabs = st.tabs(["Policyholder Details", "Hospitalization Info", "Billing Details", "Document Uploads"])
        
        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                policy_no = st.text_input("Policy Number", placeholder="e.g., POL_H_1001")
            with col2:
                holder_name = st.text_input("Policyholder / Patient Name", placeholder="e.g., Adarsh Sharma")
                
            col3, col4 = st.columns(2)
            with col3:
                age = st.number_input("Patient Age", min_value=0, max_value=120, value=30)
            with col4:
                gender = st.selectbox("Patient Gender", ["Male", "Female", "Other"])
                
            claim_data["policyholder"] = {"policy_no": policy_no, "name": holder_name}
            claim_data["patient"] = {"name": holder_name, "age": age, "gender": gender}
            
        with tabs[1]:
            col1, col2 = st.columns(2)
            with col1:
                hospital_name = st.text_input("Hospital Name", placeholder="e.g., City Hospital")
            with col2:
                diagnosis = st.text_input("Diagnosis Details / Symptoms", placeholder="e.g., Viral Fever")
                
            col3, col4 = st.columns(2)
            with col3:
                days = st.number_input("Hospitalization Duration (Days)", min_value=1, value=1)
            with col4:
                admission_type = st.selectbox("Admission Type", ["Planned", "Emergency"])
                
            claim_data["hospital"] = {"name": hospital_name, "network": True, "diagnosis": diagnosis}
            claim_data["admission"] = {"type": admission_type, "days": days}
            
        with tabs[2]:
            col1, col2, col3 = st.columns(3)
            with col1:
                total_bill = st.number_input("Total Invoice Bill Amount ($)", min_value=0.0, step=100.0)
            with col2:
                icu_charges = st.number_input("ICU Charges Included ($)", min_value=0.0, step=100.0)
            with col3:
                med_cost = st.number_input("Pharmacy / Medicine Cost ($)", min_value=0.0, step=100.0)
                
            claim_data["financial"] = {
                "total_bill": total_bill,
                "icu": icu_charges,
                "medicine": med_cost
            }
            
        with tabs[3]:
            st.subheader("📄 Upload Verified Medical Documents")
            fb = st.file_uploader("Upload Final Bill (PDF)", type=["pdf", "png", "jpg"], key="h_fb")
            mr = st.file_uploader("Upload Medical Discharge Summary", type=["pdf", "png", "jpg"], key="h_mr")
            kyc = st.file_uploader("Upload KYC ID Card", type=["pdf", "png", "jpg"], key="h_kyc")
            
            claim_data["documents"] = {
                "final_bill": fb,
                "medical_report": mr,
                "kyc": kyc
            }

    elif domain == "Vehicle":
        tabs = st.tabs(["Policyholder & Vehicle", "Accident Details", "Damage Repair Estimation", "Document Uploads"])
        
        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                policy_no = st.text_input("Policy Number", placeholder="e.g., POL_V_2002")
            with col2:
                plate = st.text_input("Vehicle License Plate Number", placeholder="e.g., KA-01-MA-1234")
                
            col3, col4 = st.columns(2)
            with col3:
                v_type = st.selectbox("Vehicle Type", ["Car", "Bike", "Truck"])
            with col4:
                idv = st.number_input("Insured Declared Value (IDV) ($)", min_value=0.0, step=1000.0)
                
            claim_data["policy"] = {"policy_no": policy_no}
            claim_data["vehicle"] = {"number": plate, "type": v_type, "idv": idv}
            
        with tabs[1]:
            col1, col2 = st.columns(2)
            with col1:
                acc_type = st.selectbox("Accident Severity Type", ["Minor", "Major"])
            with col2:
                location = st.text_input("Accident Location City", placeholder="e.g., Bengaluru")
            
            claim_data["incident"] = {"type": acc_type, "location": location}
            
        with tabs[2]:
            cost = st.number_input("Estimated Repair Invoice Bill ($)", min_value=0.0, step=500.0)
            claim_data["damage"] = {"estimated_cost": cost}
            
        with tabs[3]:
            st.subheader("📄 Upload Incident Support Documents")
            rc = st.file_uploader("Upload Vehicle RC Document", type=["pdf", "png", "jpg"], key="v_rc")
            police = st.file_uploader("Upload Police Report / FIR Copy", type=["pdf", "png", "jpg"], key="v_pol")
            images = st.file_uploader("Upload Damage Inspection Images", type=["pdf", "png", "jpg"], key="v_img")
            
            claim_data["documents"] = {
                "rc": rc,
                "police": police,
                "images": images
            }

    elif domain == "Life":
        tabs = st.tabs(["Policy Details", "Deceased Incident details", "Claim Settlement", "Document Uploads"])
        
        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                policy_no = st.text_input("Policy Number", placeholder="e.g., POL_L_3003")
            with col2:
                holder_name = st.text_input("Deceased Policyholder Name", placeholder="e.g., Robert Mercer")
                
            col3, col4 = st.columns(2)
            with col3:
                duration = st.number_input("Policy Duration Active (Years)", min_value=0.0, value=2.0)
            with col4:
                p_type = st.selectbox("Policy Structure Type", ["Term", "Whole Life"])
                
            claim_data["policy"] = {"policy_no": policy_no, "duration": duration, "type": p_type}
            claim_data["policyholder"] = {"name": holder_name}
            
        with tabs[1]:
            col1, col2 = st.columns(2)
            with col1:
                cause = st.text_input("Certified Cause of Death", placeholder="e.g., Natural Causes")
            with col2:
                date_death = st.date_input("Official Date of Death")
            
            death_cert_id = st.text_input("Death Certificate Registration Number", placeholder="e.g., DEATH_CERT_3001")
            
            claim_data["incident"] = {
                "cause": cause,
                "date": str(date_death),
                "death_certificate_id": death_cert_id
            }
            
        with tabs[2]:
            claim_amount = st.number_input("Requested Settlement Death Benefit ($)", min_value=0.0, step=5000.0)
            claim_data["financial"] = {"claim_amount": claim_amount}
            
        with tabs[3]:
            st.subheader("📄 Upload Official Certificates")
            death = st.file_uploader("Upload Death Certificate (Registry Copy)", type=["pdf", "png", "jpg"], key="l_dc")
            medical = st.file_uploader("Upload Coroner / Medical Audit Report", type=["pdf", "png", "jpg"], key="l_mr")
            
            claim_data["documents"] = {
                "death": death,
                "medical": medical
            }

    elif domain == "Financial":
        tabs = st.tabs(["Loan Account Details", "Financial Statements", "Document Uploads"])
        
        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                policy_no = st.text_input("Policy Number", placeholder="e.g., POL_F_4004")
            with col2:
                loan_id = st.text_input("Loan Registration Contract ID", placeholder="e.g., LOAN_4001")
                
            col3, col4, col5 = st.columns(3)
            with col3:
                lender = st.text_input("Lending Bank / Institution", placeholder="e.g., Apex Capital")
            with col4:
                tenure = st.number_input("Loan Tenure (Months)", min_value=1, value=60)
            with col5:
                emi = st.number_input("Monthly EMI Commitment ($)", min_value=0.0, step=100.0)
                
            claim_data["policy"] = {
                "policy_no": policy_no,
                "loan_id": loan_id,
                "lender_name": lender,
                "tenure_months": tenure,
                "emi_amount": emi
            }
            
        with tabs[1]:
            col1, col2, col3 = st.columns(3)
            with col1:
                income = st.number_input("Certified Monthly Income ($)", min_value=0.0, step=500.0)
            with col2:
                loan_amt = st.number_input("Total Disbursed Loan Principal ($)", min_value=0.0, step=1000.0)
            with col3:
                claim_amt = st.number_input("Default Loss Claim Amount ($)", min_value=0.0, step=1000.0)
                
            claim_data["financial"] = {
                "income": income,
                "loan_amount": loan_amt,
                "claim_amount": claim_amt
            }
            
        with tabs[2]:
            st.subheader("📄 Upload Financial Proofs")
            kyc = st.file_uploader("Upload KYC Card (PAN/SSN)", type=["pdf", "png", "jpg"], key="f_kyc")
            inc = st.file_uploader("Upload Salary Slips / Income Proof", type=["pdf", "png", "jpg"], key="f_inc")
            bank = st.file_uploader("Upload 6-Month Bank Account Statement", type=["pdf", "png", "jpg"], key="f_bnk")
            loan_doc = st.file_uploader("Upload Signed Loan Agreement", type=["pdf", "png", "jpg"], key="f_loan")
            
            claim_data["documents"] = {
                "kyc": kyc,
                "income_proof": inc,
                "bank_statement": bank,
                "loan_document": loan_doc
            }

    return claim_data

# =====================================================
# 🕵️ CLAIMS AUDITOR DASHBOARD (PORTAL)
# =====================================================
def render_auditor_dashboard():
    st.header("🕵️ Underwriter & Fraud Auditor Portal")
    st.caption("Inspect live registry databases and view historical analytics logs.")
    
    tab1, tab2 = st.tabs(["🗄️ SQLite Central Registry Viewer", "📈 Historical Claim Analytics"])
    
    with tab1:
        st.subheader("Distributed sandboxed Registries")
        col1, col2 = st.columns(2)
        with col1:
            db_choice = st.selectbox(
                "Select Registry Database",
                ["🏢 Insurance Company DB", "🏥 Medical Registry DB", "🚗 Motor Vehicle Registry (RTO) DB", "👤 National Death Registry DB", "💳 Credit Bureau DB"]
            )
        
        db_key_map = {
            "🏢 Insurance Company DB": "insurance",
            "🏥 Medical Registry DB": "medical",
            "🚗 Motor Vehicle Registry (RTO) DB": "motor",
            "👤 National Death Registry DB": "death",
            "💳 Credit Bureau DB": "credit"
        }
        db_key = db_key_map[db_choice]
        
        # Populate table selectbox dynamically based on database
        if db_key == "insurance":
            tables = ["Policies & Policyholders", "Claims History Logs"]
            table_query_map = {
                "Policies & Policyholders": "SELECT p.policy_number, p.kyc_id, p.domain, p.status, p.sum_assured, p.inception_date, p.tenure_months, ph.full_name, ph.age, ph.gender, ph.credit_score, ph.email FROM policies p JOIN policyholders ph ON p.kyc_id = ph.kyc_id",
                "Claims History Logs": "claims_log"
            }
        elif db_key == "medical":
            tables = ["Doctors Directory", "Hospitals Directory"]
            table_query_map = {
                "Doctors Directory": "doctor_registry",
                "Hospitals Directory": "hospital_registry"
            }
        elif db_key == "motor":
            tables = ["Vehicle Registrations", "Police Incident Reports"]
            table_query_map = {
                "Vehicle Registrations": "vehicle_registry",
                "Police Incident Reports": "police_reports"
            }
        elif db_key == "death":
            tables = ["Death Certificates Registry"]
            table_query_map = {
                "Death Certificates Registry": "death_registry"
            }
        else: # credit
            tables = ["Active Bank Loans"]
            table_query_map = {
                "Active Bank Loans": "loan_registry"
            }

        with col2:
            registry_table = st.selectbox("Select Registry Table", tables)
            
        query = table_query_map[registry_table]
        
        df = query_db_table(query, db_key=db_key)
        st.dataframe(df, use_container_width=True)
        
    with tab2:
        st.subheader("Historical Decisions & Fraud Distribution")
        claims_history = query_db_table("claims_log")
        
        if claims_history.empty or len(claims_history) == 0:
            st.info("No claims processed in this session yet.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### Verdict Volume")
                status_counts = claims_history["status"].value_counts()
                st.bar_chart(status_counts)
            with col2:
                st.markdown("##### Claim Amounts by Status ($)")
                st.bar_chart(claims_history.groupby("status")["claim_amount"].sum())

# =====================================================
# 🎯 CORE APP EXECUTION FLOW
# =====================================================
# =====================================================
# 🎯 CORE APP EXECUTION FLOW
# =====================================================
if sub_nav == "✍️ Onboard New Policy":
    st.header("✍️ Onboard New Policyholder")
    st.caption("Enter customer information to register a new policy in the central database registry.")
    
    # Domain selection first, to dynamically show other fields
    new_domain = st.selectbox("Insurance Domain", ["Health", "Vehicle", "Life", "Financial"])
    
    st.markdown("---")
    st.subheader(f"📋 {new_domain} Registration Form")
    
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Full Name", placeholder="e.g., Jane Doe")
        new_email = st.text_input("Email Address", placeholder="e.g., jane@example.com")
        new_age = st.number_input("Age", min_value=18, max_value=120, value=30)
    with col2:
        new_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        new_sum = st.number_input("Policy Sum Assured ($)", min_value=1000.0, max_value=5000000.0, value=100000.0, step=5000.0)

    # Dynamic Domain Specific Fields
    domain_fields = {}
    if new_domain == "Vehicle":
        st.markdown("---")
        st.subheader("🚗 Vehicle Registry Details")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            v_plate = st.text_input("License Plate Number", placeholder="e.g., KA-01-MA-1234")
        with col_v2:
            v_model = st.selectbox("Vehicle Model/Type", ["Car", "Bike", "Truck"])
        domain_fields["plate"] = v_plate.strip()
        domain_fields["model"] = v_model

    elif new_domain == "Financial":
        st.markdown("---")
        st.subheader("💰 Active Loan Registry Details")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            loan_id = st.text_input("Loan Agreement ID", placeholder="e.g., LOAN_4001")
            lender_name = st.text_input("Lender Institution", placeholder="e.g., Apex Capital")
        with col_f2:
            loan_type = st.selectbox("Loan Category", ["Home", "Personal", "Education", "Vehicle"])
            loan_amt = st.number_input("Loan Principal Amount ($)", min_value=1000.0, value=100000.0, step=1000.0)
        domain_fields["loan_id"] = loan_id.strip()
        domain_fields["lender_name"] = lender_name.strip()
        domain_fields["loan_type"] = loan_type
        domain_fields["loan_amount"] = loan_amt

    if st.button("Register Policy"):
        if not new_name or not new_email:
            st.error("Please provide both name and email.")
        elif new_domain == "Vehicle" and not domain_fields["plate"]:
            st.error("Please provide a vehicle license plate number.")
        elif new_domain == "Financial" and (not domain_fields["loan_id"] or not domain_fields["lender_name"]):
            st.error("Please provide both Loan ID and Lender Name.")
        else:
            import uuid
            from services.api_client import onboard_policyholder, onboard_vehicle, onboard_loan
            
            # Generate IDs
            uid = str(uuid.uuid4())[:8].upper()
            new_kyc_id = f"KYC_{uid}"
            new_pol_no = f"POL_{new_domain[0]}_{uid}"
            
            # 1. Register Policyholder & Policy
            onboard_success = onboard_policyholder(
                kyc_id=new_kyc_id,
                full_name=new_name,
                age=new_age,
                gender=new_gender,
                credit_score=720,
                email=new_email,
                policy_number=new_pol_no,
                domain=new_domain,
                sum_assured=new_sum,
                tenure_months=12
            )
            
            if not onboard_success:
                st.error("Failed to register policyholder in the registry database.")
            else:
                success_msg = "🎉 Policy Registered Successfully!"
                
                # 2. Register domain-specific records conditionally
                if new_domain == "Vehicle":
                    vehicle_success = onboard_vehicle(
                        license_plate=domain_fields["plate"],
                        registered_owner_name=new_name,
                        vehicle_model=domain_fields["model"],
                        engine_number=f"ENG{uid}",
                        chassis_number=f"CHAS{uid}",
                        registration_status="Active"
                    )
                    if vehicle_success:
                        st.info(f"Registered Vehicle Plate in RTO Motor Registry: **{domain_fields['plate']}**")
                    else:
                        st.warning("Policy registered, but failed to log vehicle plate in RTO registry.")
                        
                elif new_domain == "Financial":
                    loan_success = onboard_loan(
                        loan_id=domain_fields["loan_id"],
                        policy_number=new_pol_no,
                        lender_name=domain_fields["lender_name"],
                        loan_type=domain_fields["loan_type"],
                        loan_amount=domain_fields["loan_amount"],
                        tenure_months=36,
                        emi_amount=round(domain_fields["loan_amount"] / 36, 2)
                    )
                    if loan_success:
                        st.info(f"Registered Active Loan in Credit Registry: **{domain_fields['loan_id']}**")
                    else:
                        st.warning("Policy registered, but failed to link active loan in Credit bureau.")
                        
                st.success(success_msg)
                st.markdown(f"""
                **Customer KYC ID:** `{new_kyc_id}`
                
                **Generated Policy Number:** `{new_pol_no}`
                
                *Copy this Policy Number to file your claim!*
                """)
                
elif sub_nav == "📋 Evaluate Claim Fraud":
    claim_data = render_claimant_form()
    st.markdown("---")
    
    # Check if files uploaded
    documents = claim_data.get("documents", {})
    uploaded_keys = [k for k, v in documents.items() if v is not None]
    required_count = len(documents)
    
    if len(uploaded_keys) < required_count:
        st.warning(f"⚠️ Please upload all required files ({len(uploaded_keys)}/{required_count} uploaded) to activate claim audits.")
        st.button("🔍 Analyze Claim", disabled=True)
    else:
        if st.button("🔍 Analyze Claim", use_container_width=True):
            with st.spinner("Processing documents through OCR and verifying databases..."):
                result = run_pipeline(domain, claim_data)
                
            st.balloons()
            
            # --- DISPLAY RESULTS PANEL ---
            st.markdown("### 📊 Consolidated Audit Decision")
            
            # Metric row
            col1, col2, col3 = st.columns(3)
            with col1:
                verdict = result["decision"]
                if verdict == "Approve":
                    st.success("✅ CLAIM APPROVED")
                elif verdict == "Needs Review":
                    st.warning("⚠️ HELD FOR REVIEW")
                else:
                    st.error("❌ CLAIM REJECTED")
            with col2:
                st.metric("Fraud Anomaly Score", f"{result['fraud_score']}%")
            with col3:
                st.metric("Transaction ID", result["claim_id"])
                
            st.progress(int(result["fraud_score"]))
            
            # OCR status row
            st.markdown("#### Document Verification Details")
            if result["ocr_discrepancies"]:
                for discrepancy in result["ocr_discrepancies"]:
                    st.error(discrepancy)
            else:
                st.success(result["ocr_status"])
                
            # Executive RAG report
            st.markdown("#### 🛡️ ShieldAI Claims Audit Report")
            st.markdown(f'<div class="report-card">{result["explanation"]}</div>', unsafe_allow_html=True)
            
            # Add to history
            st.session_state.history.append({
                "id": result["claim_id"],
                "domain": domain,
                "score": result["fraud_score"],
                "decision": result["decision"]
            })

elif sub_nav == "🕵️ Registry Explorer & Analytics":
    render_auditor_dashboard()
