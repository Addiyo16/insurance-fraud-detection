def apply_rules(domain, data):

    if domain == "Health":
        from services.rules.health_rules import run
    elif domain == "Vehicle":
        from services.rules.vehicle_rules import run
    elif domain == "Life":
        from services.rules.life_rules import run
    else:
        from services.rules.financial_rules import run

    return run(data)