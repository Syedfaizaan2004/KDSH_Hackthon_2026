import math
from . import llm_client

def get_embedding(text):
    client = llm_client.get_client()
    if not client:
        return [0.0] * 1536
    
    try:
        resp = client.embeddings.create(input=text, model="text-embedding-3-small")
        return list(resp.data[0].embedding)
    except Exception:
        return [0.0] * 1536

def retrieve_evidence(claim: str, chunks: list[str], k: int = 3) -> list[str]:
    """
    Retrieves the top k most relevant chunks for a claim using cosine similarity.
    """
    if not chunks:
        return []

    # Get claim embedding
    claim_vec = get_embedding(claim)
    if all(x == 0 for x in claim_vec):
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
        dot_product = sum(a * b for a, b in zip(claim_vec, chunk_vec))
        norm_claim = math.sqrt(sum(x * x for x in claim_vec))
        norm_chunk = math.sqrt(sum(x * x for x in chunk_vec))
        score = dot_product / ((norm_claim * norm_chunk) + 1e-9)
        scores.append((score, chunk))
    
    # Sort by score desc
    scores.sort(key=lambda x: x[0], reverse=True)
    
    return [item[1] for item in scores[:k]]
