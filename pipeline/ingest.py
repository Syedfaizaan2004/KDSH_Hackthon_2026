import os
import glob

def load_file(path: str) -> str:
    """
    Reads the full content of a text file.
    
    Args:
        path (str): Absolute or relative path to the file.
        
    Returns:
        str: The full content of the file.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Error reading {path}: {e}")

def load_dataset(data_dir: str) -> dict:
    """
    Scans the data directory and loads all novels and backstories.
    
    Args:
        data_dir (str): Path to the 'data' directory.
        
    Returns:
        dict: A dictionary structure:
            {
                "novels": { "story_id": "full text...", ... },
                "backstories": { "story_id": "full text...", ... }
            }
    """
    novels_dir = os.path.join(data_dir, "novels")
    backstories_dir = os.path.join(data_dir, "backstories")
    
    dataset = {
        "novels": {},
        "backstories": {}
    }
    
    # Load Novels
    novel_files = glob.glob(os.path.join(novels_dir, "*.txt"))
    for path in novel_files:
        story_id = os.path.splitext(os.path.basename(path))[0]
        try:
            dataset["novels"][story_id] = load_file(path)
        except Exception as e:
            print(f"Warning: Failed to load novel {story_id}: {e}")

    # Load Backstories
    backstory_files = glob.glob(os.path.join(backstories_dir, "*.txt"))
    for path in backstory_files:
        basename = os.path.splitext(os.path.basename(path))[0]
        # Heuristic: story_id is usually the prefix before _backstory
        story_id = basename.replace("_backstory", "")
        # But we treat the basename as key if needed, or map to story_id
        # Ideally, we map it to the known story_ids from novels
        
        try:
            dataset["backstories"][story_id] = load_file(path)
        except Exception as e:
             print(f"Warning: Failed to load backstory {basename}: {e}")
             
    print(f"Ingest: Loaded {len(dataset['novels'])} novels and {len(dataset['backstories'])} backstories.")
    return dataset
