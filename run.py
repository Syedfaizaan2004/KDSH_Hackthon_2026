import os
import sys

def main():
    print("--- Starting Narrative Consistency Checker ---")
    
    # 1. Detect OS
    is_windows = os.name == 'nt'
    
    # 2. Inject Backend
    if is_windows:
        print("Platform: Windows detected.")
        print("Using MOCK Pathway backend (Windows)")
        
        try:
            from pipeline import mock_pathway
            # Inject into sys.modules
            sys.modules["pathway"] = mock_pathway
        except ImportError as e:
            print(f"Error loading mock pathway: {e}")
            sys.exit(1)
            
    else:
        print("Platform: Linux/macOS detected.")
        try:
            import pathway
            print("Using REAL Pathway backend")
        except ImportError:
            print("Pathway not installed. Falling back to MOCK backend (Linux/macOS fallback).")
            print("Using MOCK Pathway backend (Fallback)")
            try:
                from pipeline import mock_pathway
                sys.modules["pathway"] = mock_pathway
            except ImportError as e:
                print(f"Error loading mock pathway: {e}")
                sys.exit(1)

    # 3. Run Pipeline
    try:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        from pipeline import pathway_flow
        pathway_flow.run_pathway_server(data_dir)
        
    except Exception as e:
        print(f"\nExecution Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
