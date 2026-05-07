import pandas as pd
import random

rows = []

domains = ["Health", "Vehicle", "Life", "Financial"]

for _ in range(3000):   # 🔥 generate 3000 rows

    domain = random.choice(domains)

    amount = random.randint(5000, 500000)
    history = random.randint(0, 5)

    hospital_network = random.choice([0, 1])
    damage_cost = random.randint(0, 100000)
    policy_duration = round(random.uniform(0, 10), 2)

    income = random.randint(20000, 100000)
    loan_amount = random.randint(50000, 500000)

    # ---------------- FRAUD LOGIC ----------------
    fraud = 0

    if domain == "Health":
        if amount > 100000 and hospital_network == 0:
            fraud = 1

    elif domain == "Vehicle":
        if damage_cost > 50000 or history > 3:
            fraud = 1

    elif domain == "Life":
        if policy_duration < 1:
            fraud = 1

    elif domain == "Financial":
        if loan_amount > income * 5:
            fraud = 1

    rows.append([
        domain, amount, history, hospital_network,
        damage_cost, policy_duration, income,
        loan_amount, fraud
    ])

df = pd.DataFrame(rows, columns=[
    "domain","amount","history","hospital_network",
    "damage_cost","policy_duration","income",
    "loan_amount","fraud"
])

df.to_csv("data/raw/claims.csv", index=False)

print("✅ Large dataset created!")