# Narrative Consistency Checker - Track A

This solution implements a **Track A** submission for the KDSH 2026 Narrative Consistency Checker. It provides a modular pipeline for verifying the consistency of a character's backstory against a long-form novel using LLM-based reasoning and Retrieval Augmented Generation (RAG).

## Overview
The system determines if a hypothetical backstory overlaps causally and logically with a long-form novel. It supports:
1.  **OpenAI (Cloud)** for high-quality reasoning.
2.  **Ollama (Local)** for privacy-preserving local execution.
3.  **Mock Mode** for testing without any GPU or API keys.

## Structure
- `data/novels/`: Place full novel text here.
- `data/backstories/`: Place backstory text here. (Naming: `{story_id}_backstory.txt`)
- `pipeline/`: Core logic modules (Ingest, Claims, Retrieval, Rationale).
- `main.py`: **Primary Execution Script** (Robust Python Pipeline).
- `main_pathway.py`: Alternative Pipeline using Pathway Engine (Best for Linux/Docker).

## Components Implemented

### 1. Data Ingestion & Chunking
- **`chunker.py`**: Implements a sliding window chunker using `tiktoken` (Window: 500 tokens, Overlap: 50 tokens) to ensure context preservation across chunks. Handles missing dependencies gracefully.
- **`pathway_flow.py`**: Ingests novels and backstories from the `data/` directory.

### 2. Claim Extraction & Retrieval
- **`claims.py`**: Uses LLM to extract atomic, verifiable claims from provided backstories.
- **`retrieval.py`** / **`pathway_flow.py`**: Computes embeddings for claims and retrieves the top relevant novel excerpts using vector similarity (Cosine Similarity / KNN).

### 3. Consistency Analysis
- **`rationale.py`**: Uses LLM to analyze each claim against the retrieved chunks, determining if it is `consistent`, `contradicted`, or `neutral`.
- **`decision.py`**: Aggregates individual claim analyses. If *any* definitive contradiction is found, the story is marked as **0 (Contradict)**. Only if all checks pass is it marked **1 (Consistent)**.

## How to Run

### 1. Configuration (LLM Modes)
The system automatically detects the best available LLM backend in this order:

1.  **OpenAI (Cloud)**
    - *Requires*: `OPENAI_API_KEY` environment variable.
    - *Usage*: Best quality results.

2.  **Ollama (Local)**
    - *Requires*: Ollama running on `localhost:11434`.
    - *Usage*: Automatically used if `OPENAI_API_KEY` is missing.
    - *Tip*: Ensure you have a model pulled (e.g., `ollama pull mistral`).

3.  **Mock Mode (Testing)**
    - *Requires*: Nothing.
    - *Usage*: Automatically triggers if neither OpenAI nor Ollama is available.
    - *Behavior*: Returns deterministic dummy data based on input hashing for pipeline verification.

### 2. Execution

**Option A: Windows / Python Fallback (Recommended)**
Run the pure Python pipeline (no Pathway engine dependency):
```bash
python KDSH_2026/main.py
```
This is the most robust method for this environment. It supports OpenAI, Ollama, and Mock modes.

**Option B: Pathway Engine (Linux/WSL/Docker)**
If you are in a Pathway-compatible environment, run the streaming pipeline:
```bash
python KDSH_2026/main_pathway.py
```

### 3. Output
The pipeline will generate a CSV file in:
`KDSH_2026/results/output_results_v2.csv`

The CSV contains:
- `backstory_id`: The filename identifier of the backstory.
- `story_id`: The identifier for the narrative (e.g., `story_01`).
- `prediction`: `1` (Consistent) or `0` (Contradict).
- `rationale`: A summary of the reasoning, highlighting any contradictions found.

## Verification Data
Five example stories are included in `data/`.
Expected results (Mock Mode might differ based on hash):
- story_01 (Fire Wizard): 0 (Contradict)
- story_02 (Android): 0 (Contradict)
- story_03 (Blind): 0 (Contradict)
- story_04 (Pilot): 1 (Consistent)
- story_05 (Chef): 1 (Consistent)

## Limitations & Notes
- **Static vs Live**: The pipeline is configured to read the `data/` directory once.
- **Mock Data**: The provided `data/*.txt` files are small placeholders. For the actual hackathon, ensure the full 100k+ word novels are placed in `data/novels`.
