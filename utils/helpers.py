claim_history = {}

def check_duplicate_loan(loan_id):
    return loan_id in claim_history

def add_claim_history(loan_id):
    claim_history[loan_id] = True

def get_claim_count(loan_id):
    return 1 if loan_id in claim_history else 0