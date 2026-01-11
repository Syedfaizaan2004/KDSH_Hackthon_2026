from . import llm_client, constraints

def analyze_consistency(claim: str, chunks: list[str]) -> dict:
    """
    Analyzes if the claim is consistent with the provided chunks.
    Prioritizes deterministic rule-based constraints.
    """
    # 1. Deterministic Rule-Based Check
    rule_result = constraints.check_consistency(claim, chunks)
    if rule_result["status"] == "contradiction":
        # If explicit contradiction found by rules, trust it.
        return rule_result

    # 2. LLM / Mock Analysis
    # Join chunks but limit length if needed (though chunks[0-k] shouldn't be too huge)
    context = "\n---\n".join(chunks)
    
    prompt = f"""
    You are a consistency checker for a novel.
    
    Claim to Verify: "{claim}"
    
    Excerpts from the Novel:
    {context}
    
    Task:
    Determine if the Claim is consistent with, contradicted by, or irrelevant to the provided Excerpts.
    - If EXPLICITLY contradicted, status is "contradiction".
    - If supported or consistent, status is "consistent".
    - If the excerpts don't mention anything relevant, status is "neutral".
    
    Return a JSON object:
    {{
        "status": "consistent" | "contradiction" | "neutral",
        "reasoning": "Brief explanation citing specific parts of the text if applicable.",
        "evidence_quote": "Direct quote from the text if a contradiction or strong support is found, else null."
    }}
    """
    
    response = llm_client.structured_completion(prompt)
    if response:
        return response
        
    return {"status": "neutral", "reasoning": "LLM Analysis Failed", "evidence_quote": None}
