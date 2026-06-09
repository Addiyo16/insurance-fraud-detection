import pandas as pd
import random
import numpy as np

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

rows = []
domains = ["Health", "Vehicle", "Life", "Financial"]

# Generate 5000 claims for a rich dataset
for _ in range(5000):
    domain = random.choice(domains)
    
    # 1. Amount: Realistic right-skewed distribution
    r_amount = random.random()
    if r_amount < 0.70:
        amount = random.randint(5000, 80000)
    elif r_amount < 0.92:
        amount = random.randint(80000, 200000)
    else:
        amount = random.randint(200000, 500000)
        
    # 2. History: Most policyholders have 0 or 1 claims
    r_hist = random.random()
    if r_hist < 0.60:
        history = 0
    elif r_hist < 0.85:
        history = 1
    elif r_hist < 0.94:
        history = 2
    elif r_hist < 0.97:
        history = 3
    else:
        history = random.randint(4, 5)
        
    # 3. Hospital network flag: 85% network, 15% non-network
    hospital_network = 1 if random.random() < 0.85 else 0
    
    # 4. Damage cost: Right-skewed
    r_damage = random.random()
    if r_damage < 0.80:
        damage_cost = random.randint(0, 35000)
    elif r_damage < 0.90:
        damage_cost = random.randint(35000, 55000)
    else:
        damage_cost = random.randint(55000, 100000)
        
    # 5. Policy duration: 90% older than 1 year, 10% under 1 year
    policy_duration = round(random.uniform(0.1, 10.0), 2)
    if random.random() < 0.90:
        policy_duration = round(random.uniform(1.0, 10.0), 2)
    else:
        policy_duration = round(random.uniform(0.1, 0.99), 2)
        
    # 6. Income & Loan details
    income = random.randint(20000, 100000)
    if random.random() < 0.92:
        # Standard debt load
        loan_amount = random.randint(int(income * 0.5), int(income * 3.5))
    else:
        # High DTI debt load
        loan_amount = random.randint(int(income * 5.1), int(income * 8.0))

    # Derived flags matching the preprocessor
    non_network = int(hospital_network == 0)
    high_damage = int(damage_cost > 50000)
    early_policy = int(policy_duration < 1.0)
    income_mismatch = int(loan_amount > income * 5)

    # ---------------- PROBABILISTIC FRAUD MATRIX ----------------
    # Start with a very low base rate of fraud (industry standard)
    fraud_prob = 0.002

    # Incremental conditional probabilities (highly predictive rules)
    if domain == "Health":
        if amount > 100000 and non_network == 1:
            fraud_prob += 0.85
        elif amount > 200000:
            fraud_prob += 0.30
        if history > 3:
            fraud_prob += 0.15

    elif domain == "Vehicle":
        if high_damage == 1 and history > 3:
            fraud_prob += 0.85
        elif amount > 250000:
            fraud_prob += 0.40
        elif high_damage == 1:
            fraud_prob += 0.10

    elif domain == "Life":
        if early_policy == 1:
            fraud_prob += 0.75
        if amount > 400000:
            fraud_prob += 0.20

    elif domain == "Financial":
        if income_mismatch == 1:
            fraud_prob += 0.80
        if history > 3:
            fraud_prob += 0.15

    # Clamp probability
    fraud_prob = max(0.0, min(0.95, fraud_prob))

    # Assign binary label based on probability
    fraud = 1 if random.random() < fraud_prob else 0

    rows.append([
        domain, amount, history, hospital_network,
        damage_cost, policy_duration, income,
        loan_amount, fraud
    ])

df = pd.DataFrame(rows, columns=[
    "domain", "amount", "history", "hospital_network",
    "damage_cost", "policy_duration", "income",
    "loan_amount", "fraud"
])

print("✅ Realistic dataset generated!")
print(f"📊 Total Rows: {len(df)}")
print(f"📊 Natural Fraud Rate: {df['fraud'].mean():.2%}")

# Save raw dataset
df.to_csv("data/raw/claims.csv", index=False)