try:
    import tiktoken
except ImportError:
    tiktoken = None

def chunk_text(text: str, window_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Splits text into chunks of window_size tokens with overlap.
    Uses tiktoken if available, otherwise falls back to word count (approx 0.75 words/token).
    """
    chunks = []
    step = window_size - overlap
    
    if step <= 0:
        raise ValueError("Overlap must be smaller than window size")

    if tiktoken:
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        for i in range(0, len(tokens), step):
            chunk_tokens = tokens[i : i + window_size]
            chunk_text = enc.decode(chunk_tokens)
            chunks.append(chunk_text)
    else:
        # Fallback: Approximate 1 word ~ 1.3 tokens -> window_size tokens ~ window_size * 0.75 words
        # For simplicity, let's just use words.
        words = text.split()
        word_window = int(window_size * 0.75)
        word_step = int(step * 0.75)
        if word_step < 1: word_step = 1
        
        for i in range(0, len(words), word_step):
            chunk_words = words[i : i + word_window]
            chunks.append(" ".join(chunk_words))
    
    if not chunks:
        return [""]
        
    return chunks
