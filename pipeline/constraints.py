import re

def check_consistency(claim: str, evidence_chunks: list[str]) -> dict:
    """
    Performs deterministic, rule-based consistency checks.
    
    Args:
        claim (str): The backstory claim to verify.
        evidence_chunks (list[str]): Relevant text chunks from the novel.
        
    Returns:
        dict: {
            "status": "consistent" | "contradiction" | "neutral",
            "reasoning": "Explanation of the rule triggered.",
            "evidence_quote": "Snippet causing the decision."
        }
    """
    combined_evidence = " ".join(evidence_chunks).lower()
    claim_lower = claim.lower()
    
    # 1. Timeline Check (Years)
    # Detects if claim year conflicts with evidence year logic (simplified)
    # E.g. Claim: "Born in 1990", Evidence: "Died in 1880"
    claim_years = re.findall(r'\b(1[0-9]{3}|20[0-2][0-9])\b', claim_lower)
    evidence_years = re.findall(r'\b(1[0-9]{3}|20[0-2][0-9])\b', combined_evidence)
    
    if claim_years and evidence_years:
        # Example heuristic: If claim says "born in X" and evidence implies "active in Y" where Y < X
        # This is complex to do purely with regex, but we can flag major discrepancies if explicitly stated.
        # For this track, we'll demonstrate a simple existence check or exact contradiction if formatted.
        pass

    # 2. Behavioral Contradictions (Keywords)
    # simple antonym pairs
    antonyms = [
        ("pacifist", "fighter"),
        ("vegetarian", "meat"),
        ("teetotaler", "drank"),
        ("never", "always"),
        ("hated", "loved")
    ]
    
    for word_a, word_b in antonyms:
        # Check if claim matches one side and evidence matches the other in a contradictory context
        # This is a naive implementation; a real one needs dependency parsing.
        if word_a in claim_lower and word_b in combined_evidence:
             # simple proximity check or assuming existence implies contradiction for this demo
             return {
                 "status": "contradiction",
                 "reasoning": f"Behavioral Contradiction detected: Claim mentions '{word_a}' but Evidence mentions '{word_b}'.",
                 "evidence_quote": f"...{word_b}..."
             }
        if word_b in claim_lower and word_a in combined_evidence:
             return {
                 "status": "contradiction",
                 "reasoning": f"Behavioral Contradiction detected: Claim mentions '{word_b}' but Evidence mentions '{word_a}'.",
                 "evidence_quote": f"...{word_a}..."
             }

    # 3. Direct Negation
    # If claim says "X was Y" and evidence says "X was not Y"
    # Hard to do strictly with regex, but we can look for specific patterns.
    
    # Default to neutral if no explicit rules triggered
    return {
        "status": "neutral",
        "reasoning": "No explicit rule-based contradiction found.",
        "evidence_quote": None
    }
