# Narrative Consistency Checker

**Kharagpur Data Science Hackathon 2026 - Track A Submission**

This submission is designed specifically for Track A, emphasizing long-context narrative reasoning, causal consistency, and reproducibility.

A robust, cross-platform system designed to judge whether a hypothetical character backstory ("dossier") is globally and causally consistent with a full novel. This project implements a hybrid reasoning pipeline combining deterministic rule-based checks with optional assistive semantic analysis.

## 🚀 Key Features

*   **Universal Execution**: A single entry point (`run.py`) that works seamlessly on both **Windows** (via a custom Mock Pathway backend) and **Linux/macOS** (via the official Pathway library when available, with a Pathway-compatible fallback for full reproducibility).
*   **Dynamic Dossier Generation**: Supports optional dossier generation for synthetic testing; in the official Track-A setting, externally provided hypothetical backstories are evaluated against the novel.
*   **Hybrid Reasoning Engine**:
    *   **Constraints Module**: Deterministic, rule-based checks for timeline violations, behavioral contradictions, and direct negations.
    *   **LLM Analysis**: Optional LLM-assisted semantic analysis used only for explanation and edge cases.
*   **Clean Ingestion**: Dedicated `ingest` module for robust, full-text data loading without summarization.
*   **Transparent Output**: Produces both a summary CSV and detailed per-story JSON analysis files.

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd KDSH_2026
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: On Windows, the system will automatically use the included Mock Pathway backend, so no extra steps are required.)*

3.  **Environment Setup**:
    Create a `.env` file in the root directory if you plan to use the real OpenAI backend for the optional analysis layer:
    ```
    OPENAI_API_KEY=your_api_key_here
    ```

## ▶️ Usage

Run the entire pipeline with a single command:

```bash
python run.py
```

The system will:
1.  Detect your Operating System.
2.  Load the appropriate backend (Real vs. Mock).
3.  Ingest novels from `data/novels`.
4.  (Optional) Generate dossiers into `data/backstories` for testing if none exist.
5.  Execute the consistency checking pipeline.
6.  Save results to the `results/` directory.

## 🏗️ Pipeline Architecture

1.  **Ingest**: Loads full text of novels and backstories using `pipeline/ingest.py`.
2.  **Chunking**: Splits novels into manageable text chunks.
3.  **Claim Extraction**: Extract atomic claims from the character dossier.
4.  **Retrieval**: Uses KNN retrieval to find relevant novel excerpts for each claim.
5.  **Reasoning**:
    *   **Step A (Constraints)**: Checks for explicit contradictions (e.g., birth year > death year, "pacifist" vs "fought").
    *   **Step B (Rationale)**: Uses assistive analysis to explain semantic consistency against retrieved evidence.
6.  **Decision**: Aggregates all claim judgments into a final consistency score (0 or 1).

## 📂 Directory Structure

*   `run.py`: Main entry point.
*   `pipeline/`: Core logic modules.
    *   `ingest.py`: Data loading.
    *   `generation.py`: Optional dossier generation.
    *   `constraints.py`: Rule-based reasoning.
    *   `mock_pathway.py`: Windows compatibility layer.
    *   `chunker.py`, `claims.py`, `retrieval.py`, `decision.py`: Pipeline components.
*   `data/`: Input directory for `novels` and generated `backstories`.
*   `results/`: Output directory for `results.csv` and distinct `dossier_*.json` files.
