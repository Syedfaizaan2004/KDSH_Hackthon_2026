import os
import glob
import csv
from pipeline import chunker, claims, retrieval, rationale, decision

def main():
    print("--- Starting Narrative Consistency Checker (Python Engine) ---")
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    novels_dir = os.path.join(data_dir, "novels")
    backstories_dir = os.path.join(data_dir, "backstories")
    output_path = os.path.join(base_dir, "results", "results.csv")
    
    # Ensure results dir
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Find all backstories
    backstory_files = glob.glob(os.path.join(backstories_dir, "*.txt"))
    
    results = []
    
    print(f"Found {len(backstory_files)} backstories.")
    
    for backstory_path in backstory_files:
        backstory_id = os.path.splitext(os.path.basename(backstory_path))[0]
        
        # Heuristic: Extract story_id from backstory_id
        # Expecting format: "story_01_backstory" -> "story_01"
        # Or generally: The prefix matches a novel filename
        if "_backstory" in backstory_id:
            story_id = backstory_id.replace("_backstory", "")
        else:
            # Fallback or custom logic if naming differs
            # For now assume the first part until the last underscore is the story ID?
            # Or just assume direct mapping if possible.
            story_id = backstory_id
            
        print(f"Processing Backstory: {backstory_id} (Linked Novel: {story_id})...")
        
        # Load Novel
        novel_path = os.path.join(novels_dir, f"{story_id}.txt")
        if not os.path.exists(novel_path):
             print(f"  Warning: Linked novel {story_id}.txt not found. Skipping.")
             continue
             
        with open(novel_path, "r", encoding="utf-8") as f:
            novel_text = f.read()
            
        with open(backstory_path, "r", encoding="utf-8") as f:
            backstory_text = f.read()
            
        # --- Pipeline Steps ---
        
        # 1. Chunking
        chunks = chunker.chunk_text(novel_text)
        
        # 2. Extract Claims
        extracted_claims = claims.extract_claims(backstory_text)
        if not extracted_claims:
            print(f"  No claims extracted for {backstory_id}.")
            results.append([backstory_id, story_id, 1, "No verifiable claims found."])
            continue
            
        # 3. Analyze Claims
        analyses = []
        for claim in extracted_claims:
            # Retrieve Evidence
            relevant_chunks = retrieval.retrieve_evidence(claim, chunks, k=3)
            
            # Analyze Consistency
            analysis = rationale.analyze_consistency(claim, relevant_chunks)
            analyses.append(analysis)
            
        # 4. Decide
        prediction, reason = decision.aggregate_results(analyses)
        
        print(f"  Result: {prediction} ({reason})")
        results.append([backstory_id, story_id, prediction, reason])

    # Write Results
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["backstory_id", "story_id", "prediction", "rationale_summary"])
        writer.writerows(results)
        
    print(f"--- Completed. Results saved to {output_path} ---")

if __name__ == "__main__":
    main()
