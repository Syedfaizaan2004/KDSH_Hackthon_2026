from . import llm_client

def extract_claims(backstory_text: str) -> list[str]:
    """
    Extracts atomic, verifiable claims from the backstory using LLM.
    """
    prompt = f"""
    You are an expert literary analyst. 
    Analyze the following character backstory and extract a list of atomic, verifiable claims about the character's past, beliefs, or actions.
    Each claim should be a standalone sentence that can be checked against a novel's text for consistency.
    
    Backstory:
    {backstory_text}
    
    Return a JSON object with a single key "claims" containing a list of strings.
    Example: {{ "claims": ["Born in 1990", "Hates broccoli", "Worked as a spy"] }}
    """
    
    response = llm_client.structured_completion(prompt)
    if response and "claims" in response:
        return response["claims"]
    
    # Fallback if LLM fails
    return []
