import os
import glob
import csv
import json
from pipeline import chunker, claims, retrieval, rationale, decision, generation

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
    
    # Find all novels
    novel_files = glob.glob(os.path.join(novels_dir, "*.txt"))
    
    results = []
    
    print(f"Found {len(novel_files)} novels. Starting processing...")
    
    for novel_path in novel_files:
        story_id = os.path.splitext(os.path.basename(novel_path))[0]
        print(f"\nProcessing Story: {story_id}...")

        # 1. Load Novel
        with open(novel_path, "r", encoding="utf-8") as f:
            novel_text = f.read()

        # 2. Generate Dossier (Dynamic)
        print(f"  Generating dossier for {story_id}...")
        try:
            dossier_text = generation.generate_dossier(novel_text)
        except Exception as e:
            print(f"  Error generating dossier: {e}")
            dossier_text = "Error: Could not generate dossier."

        # Save generated dossier
        backstory_id = f"{story_id}_backstory"
        backstory_path = os.path.join(backstories_dir, f"{backstory_id}.txt")
        with open(backstory_path, "w", encoding="utf-8") as f:
            f.write(dossier_text)
            
        print(f"  Dossier saved to {backstory_path}")

        # --- Pipeline Steps ---
        
        # 3. Chunking
        chunks = chunker.chunk_text(novel_text)
        
        # 4. Extract Claims
        extracted_claims = claims.extract_claims(dossier_text)
        if not extracted_claims:
            print(f"  No claims extracted for {backstory_id}.")
            results.append([backstory_id, story_id, 1, "No verifiable claims found."])
            continue
            
        # 5. Analyze Claims
        analyses = []
        for claim in extracted_claims:
            # Retrieve Evidence
            relevant_chunks = retrieval.retrieve_evidence(claim, chunks, k=3)
            
            # Analyze Consistency
            analysis = rationale.analyze_consistency(claim, relevant_chunks)
            analyses.append(analysis)
            
        # 6. Decide
        prediction, reason = decision.aggregate_results(analyses)
        
        # Save JSON Analysis
        json_output = {
            "story_id": story_id,
            "overall_judgment": prediction,
            "analysis": []
        }
        
        for i, claim in enumerate(extracted_claims):
            # Safe access to analyses[i] assuming 1:1 mapping
            if i < len(analyses):
                a = analyses[i]
                status_map = { "consistent": 1, "contradiction": 0, "neutral": -1 }
                
                # Heuristic mapping for display
                status_label = a.get("status", "neutral").capitalize()
                judgment_val = status_map.get(a.get("status", "neutral").lower(), -1)
                
                item = {
                    "judgment": judgment_val,
                    "analysis": a.get("reasoning", ""),
                    "status_label": status_label,
                    "claim": claim,
                    "evidence_quote": a.get("evidence_quote")
                }
                json_output["analysis"].append(item)
        
        json_path = os.path.join(base_dir, "results", f"dossier_{story_id}.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_output, f, indent=2)
            print(f"  JSON Analysis saved to {json_path}")
        except Exception as e:
            print(f"  Error saving JSON analysis: {e}")

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
