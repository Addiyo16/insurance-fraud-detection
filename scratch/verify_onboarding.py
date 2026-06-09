import sys
import os
import requests

# Fix path to import modules
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from utils.database_setup import init_distributed_dbs as init_db
from services.api_client import (
    onboard_policyholder,
    onboard_vehicle,
    onboard_loan,
    get_policy_details,
    verify_vehicle,
    get_loan_details
)

def run_onboarding_tests(api_online=True):
    mode_str = "ONLINE (REST API)" if api_online else "OFFLINE (SQLite Fallback)"
    print(f"\n==============================================================")
    print(f"       TESTING ONBOARDING FLOW: {mode_str}")
    print(f"==============================================================")

    # 1. Health Onboarding (Should only write to insurance DB)
    print("🔹 Onboarding Health Policyholder...")
    h_kyc = "KYC_HEALTH_TEST"
    h_pol = "POL_H_TEST"
    success_h = onboard_policyholder(
        kyc_id=h_kyc,
        full_name="Alice HealthTester",
        age=32,
        gender="Female",
        credit_score=710,
        email="alice@test.com",
        policy_number=h_pol,
        domain="Health",
        sum_assured=250000.0
    )
    print("  Onboarding Status:", "SUCCESS" if success_h else "FAILED")
    
    # Verify records in Insurance DB
    pol_details = get_policy_details(h_pol)
    if pol_details and pol_details["full_name"] == "Alice HealthTester":
        print("  ✅ Policy record verified in Insurance DB!")
    else:
        print("  ❌ Policy record verification FAILED in Insurance DB!")

    # 2. Vehicle Onboarding (Should write to Insurance and Motor DB)
    print("\n🔹 Onboarding Vehicle Policyholder...")
    v_kyc = "KYC_VEH_TEST"
    v_pol = "POL_V_TEST"
    v_plate = "KA-01-TEST-1234"
    success_v_pol = onboard_policyholder(
        kyc_id=v_kyc,
        full_name="Bob MotorTester",
        age=40,
        gender="Male",
        credit_score=750,
        email="bob@test.com",
        policy_number=v_pol,
        domain="Vehicle",
        sum_assured=150000.0
    )
    success_v_reg = onboard_vehicle(
        license_plate=v_plate,
        registered_owner_name="Bob MotorTester",
        vehicle_model="Car",
        engine_number="ENG_TEST_123",
        chassis_number="CHAS_TEST_123",
        registration_status="Active"
    )
    print("  Policy Onboard Status:", "SUCCESS" if success_v_pol else "FAILED")
    print("  Vehicle Reg Status   :", "SUCCESS" if success_v_reg else "FAILED")

    # Verify records in Insurance and Motor DB
    pol_details_v = get_policy_details(v_pol)
    veh_details = verify_vehicle(v_plate)
    if pol_details_v and pol_details_v["full_name"] == "Bob MotorTester":
        print("  ✅ Policy record verified in Insurance DB!")
    else:
        print("  ❌ Policy record verification FAILED in Insurance DB!")
        
    if veh_details and veh_details["registered_owner_name"] == "Bob MotorTester":
        print("  ✅ Vehicle record verified in Motor Registry DB!")
    else:
        print("  ❌ Vehicle record verification FAILED in Motor Registry DB!")

    # 3. Financial Onboarding (Should write to Insurance and Credit DB)
    print("\n🔹 Onboarding Financial Policyholder...")
    f_kyc = "KYC_FIN_TEST"
    f_pol = "POL_F_TEST"
    f_loan = "LOAN_TEST_9999"
    success_f_pol = onboard_policyholder(
        kyc_id=f_kyc,
        full_name="Charlie LoanTester",
        age=50,
        gender="Male",
        credit_score=680,
        email="charlie@test.com",
        policy_number=f_pol,
        domain="Financial",
        sum_assured=300000.0
    )
    success_f_loan = onboard_loan(
        loan_id=f_loan,
        policy_number=f_pol,
        lender_name="Apex Capital",
        loan_type="Personal",
        loan_amount=120000.0,
        tenure_months=24,
        emi_amount=5000.0
    )
    print("  Policy Onboard Status:", "SUCCESS" if success_f_pol else "FAILED")
    print("  Loan Reg Status      :", "SUCCESS" if success_f_loan else "FAILED")

    # Verify records in Insurance and Credit DB
    pol_details_f = get_policy_details(f_pol)
    loan_details = get_loan_details(f_loan)
    if pol_details_f and pol_details_f["full_name"] == "Charlie LoanTester":
        print("  ✅ Policy record verified in Insurance DB!")
    else:
        print("  ❌ Policy record verification FAILED in Insurance DB!")
        
    if loan_details and loan_details["lender_name"] == "Apex Capital":
        print("  ✅ Loan record verified in Credit Bureau DB!")
    else:
        print("  ❌ Loan record verification FAILED in Credit Bureau DB!")

if __name__ == "__main__":
    # Reset DBs
    init_db()
    
    # 1. Run Offline tests
    run_onboarding_tests(api_online=False)
    
    # 2. Run Online tests (requires FastAPI server running in background)
    try:
        r = requests.get("http://127.0.0.1:8000/api/policy/POL_H_1001", timeout=0.5)
        server_running = True
    except Exception:
        server_running = False
        
    if server_running:
        init_db()  # Reset DBs again for a clean online test
        run_onboarding_tests(api_online=True)
    else:
        print("\n⚠️ Note: Skipping Online REST tests because the FastAPI server on port 8000 is not running.")
