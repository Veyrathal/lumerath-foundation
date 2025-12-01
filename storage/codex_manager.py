import os
import json

STORAGE_PATH = os.path.join(os.path.dirname(__file__), "codex")

def list_entries():
    """List all codex files."""
    return [f for f in os.listdir(STORAGE_PATH) if f.endswith(".json")]

def read_entry(filename):
    """Read a specific codex entry."""
    path = os.path.join(STORAGE_PATH, filename)
    if not os.path.exists(path):
        return {"error": "File not found"}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_entry(filename, data):
    """Save or update a codex entry."""
    path = os.path.join(STORAGE_PATH, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return {"message": f"{filename} saved successfully"}
