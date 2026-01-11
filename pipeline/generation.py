import json
from . import llm_client

def generate_dossier(novel_text: str, model: str = "gpt-4o") -> str:
    """
    Generates a dossier (backstory) for the main character or a significant character 
    from the provided novel text.
    """
    client = llm_client.get_client()
    
    # We might need to truncate the text to fit context, 
    # though for a real app we'd want smart extraction.
    # Taking first 15000 chars as a heuristic for context.
    context_text = novel_text[:15000]

    prompt = f"""
    You are an expert literary analyst. Read the following excerpt from a novel and generate a structured dossier for the protagonist or a key character.
    The dossier should act as a backstory claim sheet.
    
    Novel Excerpt:
    {context_text}
    
    Instructions:
    1. Identify the main character.
    2. Extract key facts, history, and personality traits.
    3. Format the output as a plain text narrative that lists these points clearly.
    4. Do NOT use Markdown formatting or JSON. Just plain paragraphs.
    
    Output:
    """
    
    # We use simple completion here as we want text, not JSON structure necessarily,
    # but our llm_client.structured_completion is built for JSON.
    # Let's adjust usage to either add a new method or use the raw client if accessible,
    # OR we just ask for JSON and parse it back to text.
    # Let's stick to the existing pattern: define a text-generation helper or use structured but ask for a "dossier" field.
    
    json_prompt = f"""
    You are an expert literary analyst. Read the following excerpt from a novel and generate a structured dossier for the protagonist or a key character.
    
    Novel Excerpt:
    {context_text}
    
    Return a JSON object with a single key "dossier" containing the full text of the character backstory.
    """
    
    response = llm_client.structured_completion(json_prompt, model=model)
    
    if response and "dossier" in response:
        return response["dossier"]
    
    return "Error: Could not generate dossier."
