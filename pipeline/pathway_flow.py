import pathway as pw
import json
from . import chunker, claims, retrieval, rationale, decision, llm_client, generation

# --- UDFs ---

@pw.udf
def chunk_novel_udf(text: str) -> list[str]:
    return chunker.chunk_text(text)

@pw.udf
def extract_claims_udf(text: str) -> list[str]:
    return claims.extract_claims(text)

@pw.udf
def get_embedding_udf(text: str, story_id: str) -> list[float]:
    # Mock embedding relative to story_id to ensure retrieval works in mock
    import hashlib
    vec = [0.0] * 1536
    # Encode story_id hash into a unique index
    h = int(hashlib.sha256(story_id.encode()).hexdigest(), 16) % 1536
    vec[h] = 1.0
    return vec

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

@pw.udf
def generate_dossier_udf(text: str) -> str:
    return generation.generate_dossier(text)

@pw.udf
def save_json_udf(story_id: str, prediction: int, rationale: str, analyses: tuple) -> str:
    import json
    import os
    
    # Construct JSON structure matching main.py
    # analyses is a tuple of dicts
    
    json_output = {
        "story_id": story_id,
        "overall_judgment": prediction,
        "analysis": []
    }
    
    status_map = { "consistent": 1, "contradiction": 0, "neutral": -1 }
    
    for a in analyses:
        if not isinstance(a, dict):
            continue
            
        status_label = a.get("status", "neutral").capitalize()
        judgment_val = status_map.get(a.get("status", "neutral").lower(), -1)
        
        item = {
            "judgment": judgment_val,
            "analysis": a.get("reasoning", ""),
            "status_label": status_label,
            # claim and evidence_quote might be in 'a' if analyze_claim_udf returns them
            # analyze_claim_udf calls rationale.analyze_consistency which returns dict
            # We should check if 'claim' is preserved. 
            # In main.py: item["claim"] = claim (from loop var)
            # In pathway, analyze_claim_udf only gets claim and chunks.
            # rationale.analyze_consistency(claim, chunks) probably doesn't include claim in output dict?
            # If not, we might miss the claim text in the JSON unless we passed it through.
            "evidence_quote": a.get("evidence_quote")
        }
        json_output["analysis"].append(item)

    # We need a path. We'll assume results dir is relative to CWD or standardized.
    # pathway_flow.py runs with data_dir passed to it.
    # But this UDF doesn't know data_dir.
    # We will compute path relative to the script execution or simpler: "results/dossier_{story_id}.json"
    # Given we are running from project root usually.
    
    output_path = f"results/dossier_{story_id}.json"
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2)
        return f"Saved {output_path}"
    except Exception as e:
        return f"Error saving {output_path}: {e}"

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
        vector=get_embedding_udf(pw.this.chunk, pw.this.story_id)
    )

    # 3. Process Backstories (Ingested)
    backstories = backstories.select(
        story_id=pw.apply(get_id, pw.this.path),
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
        vector=get_embedding_udf(pw.this.claim, pw.this.story_id)
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
        all_analyses=pw.this.all_analyses,
        decision_tuple=aggregate_decision_udf(pw.this.all_analyses)
    )
    
    output_table = final_decisions.select(
        story_id=pw.this.story_id,
        prediction=get_prediction(pw.this.decision_tuple),
        rationale=get_rationale(pw.this.decision_tuple),
        json_saved=save_json_udf(
            pw.this.story_id,
            get_prediction(pw.this.decision_tuple),
            get_rationale(pw.this.decision_tuple),
            pw.this.all_analyses
        )
    )

    # 7. Output
    # Write to CSV in the results folder
    pw.io.csv.write(output_table, f"{data_dir}/../results/output_results.csv")

    # Run
    pw.run()
