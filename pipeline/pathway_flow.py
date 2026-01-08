import pathway as pw
import json
from . import chunker, claims, retrieval, rationale, decision, llm_client

# --- UDFs ---

@pw.udf
def chunk_novel_udf(text: str) -> list[str]:
    return chunker.chunk_text(text)

@pw.udf
def extract_claims_udf(text: str) -> list[str]:
    return claims.extract_claims(text)

@pw.udf
def get_embedding_udf(text: str) -> list[float]:
    client = llm_client.get_client()
    if client:
        try:
            # Use a smaller/faster model if possible, or consistent with usage
            resp = client.embeddings.create(input=text, model="text-embedding-3-small")
            return resp.data[0].embedding
        except Exception:
            pass
    # Return dummy vector if failed or mock
    return [0.0] * 1536

@pw.udf
def analyze_claim_udf(claim: str, chunks: list[str]) -> dict:
    return rationale.analyze_consistency(claim, chunks)

@pw.udf
def aggregate_decision_udf(analyses: list[dict]) -> tuple[int, str]:
    return decision.aggregate_results(analyses)

@pw.udf
def get_prediction(decision_tuple: tuple[int, str]) -> int:
    return decision_tuple[0]

@pw.udf
def get_rationale(decision_tuple: tuple[int, str]) -> str:
    return decision_tuple[1]

# --- Pipeline ---

def run_pathway_server(data_dir: str):
    """
    Sets up and runs the Pathway dataflow.
    """
    
    # 1. Input Sources
    novels = pw.io.fs.read(f"{data_dir}/novels", format="binary", mode="static", with_metadata=True)
    backstories = pw.io.fs.read(f"{data_dir}/backstories", format="binary", mode="static", with_metadata=True)

    # 2. Preprocess Novels
    def get_id(path):
        import os
        base = os.path.basename(path)
        # Assuming format "story_01.txt" or similar
        return os.path.splitext(base)[0]

    novels = novels.select(
        story_id=pw.apply(get_id, pw.this.path),
        text=pw.this.data.decode("utf-8")
    )
    
    # Chunking
    novel_chunks = novels.select(
        story_id=pw.this.story_id,
        chunk=chunk_novel_udf(pw.this.text)
    ).flatten(pw.this.chunk)
    
    # Add Embeddings for KNN
    novel_vectors = novel_chunks.select(
        story_id=pw.this.story_id,
        chunk=pw.this.chunk,
        vector=get_embedding_udf(pw.this.chunk)
    )

    # 3. Preprocess Backstories
    def get_bs_id(path):
        import os
        base = os.path.basename(path)
        # Assuming format "story_01_backstory.txt" or similar
        return base.replace("_backstory", "").replace(".txt", "")

    backstories = backstories.select(
        story_id=pw.apply(get_bs_id, pw.this.path),
        text=pw.this.data.decode("utf-8")
    )

    # Extract Claims
    claims_table = backstories.select(
        story_id=pw.this.story_id,
        claim=extract_claims_udf(pw.this.text)
    ).flatten(pw.this.claim)

    # Add Embeddings
    claim_vectors = claims_table.select(
        story_id=pw.this.story_id,
        claim=pw.this.claim,
        vector=get_embedding_udf(pw.this.claim)
    )

    # 4. Retrieval (KNN)
    # Join on KNN. Retrieve top k relevant chunks for every claim.
    matches = claim_vectors.join(
        novel_vectors,
        pw.knn(claim_vectors.vector, novel_vectors.vector, k=5),
        right_name="novel"
    )
    
    # Filter for correct story (Strict Context)
    matches = matches.filter(pw.this.story_id == pw.this.novel_story_id)
    
    # 5. Grouping & Analysis per Claim
    grouped_by_claim = matches.groupby(pw.this.story_id, pw.this.claim).reduce(
        relevant_chunks=pw.reducers.tuple(pw.this.novel_chunk)
    )

    claim_analyses = grouped_by_claim.select(
        story_id=pw.this.story_id,
        claim=pw.this.claim,
        analysis=analyze_claim_udf(pw.this.claim, pw.this.relevant_chunks)
    )
    
    # 6. Grouping & Aggregation per Story
    grouped_by_story = claim_analyses.groupby(pw.this.story_id).reduce(
        all_analyses=pw.reducers.tuple(pw.this.analysis)
    )
    
    final_decisions = grouped_by_story.select(
        story_id=pw.this.story_id,
        decision_tuple=aggregate_decision_udf(pw.this.all_analyses)
    )
    
    output_table = final_decisions.select(
        story_id=pw.this.story_id,
        prediction=get_prediction(pw.this.decision_tuple),
        rationale=get_rationale(pw.this.decision_tuple)
    )

    # 7. Output
    # Write to CSV in the results folder
    pw.io.csv.write(output_table, f"{data_dir}/../results/output_results.csv")

    # Run
    pw.run()
