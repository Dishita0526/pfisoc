import json
import os
import time 

# temporary file path for mock persistence
MOCK_DB_PATH = os.path.join(os.getcwd(), "mock_analyzed_tasks.json")

# check for existing analysis by file hash 
def get_analysis_id_by_hash(file_hash: str) -> str | None:
    """Checks the mock DB for a previous analysis matching the file hash."""
    if not os.path.exists(MOCK_DB_PATH):
        return None

    try:
        with open(MOCK_DB_PATH, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("WARNING: Mock DB file corrupt, returning None.")
        return None
    
    for record in reversed(data): 
        if record.get('file_hash') == file_hash:
            return record.get('app_id') 
            
    return None

# save analyzed tasks 
def save_analyzed_tasks(upload_id: str, file_hash: str, chunks: list[dict], tasks: list[dict]):
    """Saves the tasks to a local file, including the file hash."""
    print(f"MOCK DB: Saving {len(tasks)} tasks for upload_id: {upload_id}")
    
    # load existing data or initialize an empty list
    data = []
    if os.path.exists(MOCK_DB_PATH):
        try:
            with open(MOCK_DB_PATH, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("WARNING: Mock DB file corrupt, resetting.")
            data = []

    audit_record = {
        "app_id": upload_id, # Using the unique ID for the specific upload
        "file_hash": file_hash, # new field for deduplication
        "source_document_chunks_count": len(chunks),
        "analyzed_tasks": tasks,
        "timestamp": time.time()
    }
    
    data.append(audit_record)

    # Save the updated data
    with open(MOCK_DB_PATH, 'w') as f:
        json.dump(data, f, indent=2)

# --- Modified Function: Get latest analyzed tasks (uses upload_id) ---
def get_latest_analyzed_tasks(upload_id: str) -> list[dict]:
    """Retrieves the tasks for a specific upload_id."""
    if not os.path.exists(MOCK_DB_PATH):
        return []

    try:
        with open(MOCK_DB_PATH, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return []
    
    # Find the specific record matching the upload_id
    for record in reversed(data): 
        if record.get('app_id') == upload_id:
            return record.get("analyzed_tasks", [])
            
    return []
