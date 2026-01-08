def violates_constraints(claim, evidence):
    for e in evidence:
        if "avoids institutions" in claim.lower():
            if "volunteered" in e["text"].lower():
                return True
            if "accepted" in e["text"].lower():
                return True
    return False
