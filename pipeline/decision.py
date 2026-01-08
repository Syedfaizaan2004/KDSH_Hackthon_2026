import json

def aggregate_results(analyses: list[dict]) -> tuple[int, str]:
    """
    Aggregates a list of claim analysis dictionaries into a final decision.
    
    Returns:
        (prediction, rationale_summary)
        prediction: 1 (Consistent) or 0 (Contradict)
        rationale: String explanation
    """
    contradictions = []
    consistencies = []
    
    for analysis in analyses:
        status = analysis.get("status", "neutral")
        if status == "contradiction":
            contradictions.append(analysis)
        elif status == "consistent":
            consistencies.append(analysis)
            
    if contradictions:
        # If any contradiction exists, the backstory is inconsistent.
        # We cite the first contradiction as the primary reason.
        primary = contradictions[0]
        reason = f"Contradiction detected: {primary.get('reasoning')} (Evidence: {primary.get('evidence_quote')})"
        return 0, reason
        
    if consistencies:
        return 1, "Backstory is consistent with retrieved narrative events."
        
    # Default if no strong signal
    return 1, "No explicit contradictions found in narrative."
