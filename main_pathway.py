import os
import sys

# Ensure pipeline is importable
sys.path.append(os.path.join(os.path.dirname(__file__)))

from pipeline import pathway_flow

def main():
    print("--- Starting Narrative Consistency Checker (Pathway Engine) ---")
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    
    # Check for Pathway
    try:
        import pathway
    except ImportError:
        print("Error: Pathway not installed. Please run `pip install pathway`.")
        return

    # Check Environment
    # On Windows, Pathway behavior is limited/unsupported for some features.
    if os.name == 'nt':
        print("Warning: Running Pathway on Windows may have limited support or require Docker/WSL.")
        print("Attempting to run...")

    try:
        pathway_flow.run_pathway_server(data_dir)
    except Exception as e:
        print(f"Pathway Execution Error: {e}")
        print("Note: If this is a platform issue, please use `main.py` for the standard Python pipeline.")

if __name__ == "__main__":
    main()
