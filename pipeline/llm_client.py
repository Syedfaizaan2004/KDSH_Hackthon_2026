import os
import json
import random
from openai import OpenAI, APIConnectionError
from dotenv import load_dotenv

load_dotenv()

_client = None
_mode = "unknown"

class MockClient:
    """
    A mock client that simulates LLM responses for testing/demo purposes.
    """
    def __init__(self):
        print("--- Using MOCK LLM Client ---")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                # We won't actually monitor args here for simple mock
                return None 

    class embeddings:
        @staticmethod
        def create(*args, **kwargs):
            # Return dummy embedding
            class Data:
                embedding = [0.1] * 1536
            class Resp:
                data = [Data()]
            return Resp()

def get_client():
    global _client, _mode
    if _client is not None:
        return _client

    # 1. Try OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        _client = OpenAI(api_key=api_key)
        _mode = "openai"
        return _client

    # 2. Try Local Ollama
    try:
        base_url = "http://localhost:11434/v1"
        # Test connection structure
        # We use a short timeout to check if server is up
        client = OpenAI(base_url=base_url, api_key="ollama")
        try:
           client.models.list()
           _client = client
           _mode = "ollama"
           print(f"--- Connected to Local LLM at {base_url} ---")
           return _client
        except Exception:
           pass # Ollama not running or reachable
    except Exception:
        pass

    # 3. Fallback to Mock
    _client = MockClient()
    _mode = "mock"
    return _client

def structured_completion(prompt, model="gpt-4o"):
    """
    Helper for JSON response generation.
    Returns parsed dict or None on failure.
    """
    client = get_client()

    if _mode == "mock":
        return _mock_response(prompt)

    # For Ollama, we might need a different model name if gpt-4o is passed
    # Just use 'llama3' or similar if mode is ollama, or let user configure it.
    # For simplicity, if mode is ollama, we override model if strictly needed,
    # but often Ollama proxies accept any string or specific model names available.
    # We'll default to 'mistral' or 'llama2' if not specified, 
    # but here we keep the param or use a safe default for local.
    current_model = model
    if _mode == "ollama":
        current_model = "mistral" # Common default, assumes user has it pulled
    
    try:
        response = client.chat.completions.create(
            model=current_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        # Local models might include markdown fences (```json ... ```)
        if "```" in content:
            content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"LLM Error ({_mode}): {e}")
        if _mode == "ollama":
             print("Tip: Ensure you have the model pulled (e.g. `ollama pull mistral`)")
        return None

def _mock_response(prompt):
    """
    Generates deterministic mock responses based on prompt content.
    """
    prompt_lower = prompt.lower()
    
    # 1. Claims extraction
    if "extract a list of atomic" in prompt_lower:
        # Extract the Backstory part from the prompt
        try:
            # We assume the prompt format defined in claims.py
            start_marker = "Backstory:"
            start_idx = prompt.find(start_marker)
            if start_idx != -1:
                backstory_part = prompt[start_idx + len(start_marker):].strip()
                # Simple sentence splitter
                sentences = [s.strip() for s in backstory_part.split('.') if len(s.strip()) > 10]
                # Return up to 3 sentences as claims
                return {"claims": sentences[:3] if sentences else ["Mock claim from empty backstory"]}
        except Exception:
            pass
            
        return {
            "claims": [
                "Mock claim: Backstory extraction failed.",
            ]
        }
    
    # 2. Consistency Analysis
    if "consistency checker" in prompt_lower:
        # Deterministic result based on string hash of the prompt
        # This ensures the same input gives the same output, but different inputs differ.
        h = sum(ord(c) for c in prompt[:500]) # simple hash
        
        if h % 3 == 0:
             return {
                "status": "contradiction",
                "reasoning": "Mock analysis: Detected a logical conflict in the narrative based on input hash.",
                "evidence_quote": "Mock evidence quote derived from text."
            }
        
        return {
            "status": "consistent",
            "reasoning": "Mock analysis: The claim aligns with the retrieved context.",
            "evidence_quote": None
        }
        
    return None
