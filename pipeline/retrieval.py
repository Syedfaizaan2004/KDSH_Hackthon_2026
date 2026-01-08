import numpy as np
from . import llm_client

def get_embedding(text):
    client = llm_client.get_client()
    if not client:
        return np.zeros(1536)
    
    try:
        resp = client.embeddings.create(input=text, model="text-embedding-3-small")
        return np.array(resp.data[0].embedding)
    except Exception:
        return np.zeros(1536)

def retrieve_evidence(claim: str, chunks: list[str], k: int = 3) -> list[str]:
    """
    Retrieves the top k most relevant chunks for a claim using cosine similarity.
    """
    if not chunks:
        return []

    # Get claim embedding
    claim_vec = get_embedding(claim)
    if np.all(claim_vec == 0):
        # Fallback if no embeddings: random or keyword
        # Just return random chunks for demo if mock fails silently
        return chunks[:k]

    # chunk embeddings (In a real app, cache these!)
    # For this demo, we'll re-compute or mock.
    # To avoid being too slow, checks if we are in Mock mode in llm_client.
    
    scores = []
    for chunk in chunks:
        chunk_vec = get_embedding(chunk)
        # Cosine similarity
        score = np.dot(claim_vec, chunk_vec) / (np.linalg.norm(claim_vec) * np.linalg.norm(chunk_vec) + 1e-9)
        scores.append((score, chunk))
    
    # Sort by score desc
    scores.sort(key=lambda x: x[0], reverse=True)
    
    return [item[1] for item in scores[:k]]
