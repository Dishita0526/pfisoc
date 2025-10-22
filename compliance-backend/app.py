import os
import json
import tempfile
import uuid
import hashlib 
from flask import Flask, request, jsonify
from flask_cors import CORS

from extract import extract_and_chunk_pdf 
from ai_parser import analyze_compliance_chunks 
from db_manager import save_analyzed_tasks, get_latest_analyzed_tasks, get_analysis_id_by_hash 

from dotenv import load_dotenv
load_dotenv()  

# --- Global Environment Variables ---
__app_id = os.environ.get('APP_ID', 'default-app-id') 
__api_key = os.environ.get('GEMINI_API_KEY', '')

print("DEBUG: Loaded API key (len):", len(__api_key))
    
# --- Configuration ---
app = Flask(__name__)
CORS(app) 
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir() 

# --- Utility Function: Calculate File Hash ---
def calculate_file_hash(filepath: str) -> str:
    """Calculates the SHA256 hash of the file content for deduplication."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            # Read and update hash string in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                hash_sha256.update(byte_block)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"Error calculating hash: {e}")
        # Return a non-standard hash to force re-analysis if hashing fails
        return str(uuid.uuid4()) 

@app.route('/', methods=['GET'])
def home():
    """Simple status check for the backend."""
    return "Compliance Backend Running Successfully!"

@app.route('/upload_regulation', methods=['POST'])
def upload_regulation():
    """
    Handles PDF upload, checks for existing analysis, and runs AI analysis if needed.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400
    
    # 1. Create a unique ID for this specific upload/analysis job
    current_upload_id = str(uuid.uuid4())
    
    if file and file.filename.endswith('.pdf'):
        temp_dir = app.config['UPLOAD_FOLDER']
        # Use the current_upload_id to create a unique temporary filename
        temp_filename = os.path.join(temp_dir, current_upload_id + file.filename)
        
        try:
            # A. Save the file temporarily
            file.save(temp_filename)

            # B. Calculate File Hash
            file_hash = calculate_file_hash(temp_filename)
            
            # C. DEDUPLICATION CHECK (CRITICAL NEW STEP)
            existing_upload_id = get_analysis_id_by_hash(file_hash)
            
            if existing_upload_id:
                print(f"DEDUPE HIT: File (Hash: {file_hash[:8]}...) previously analyzed under ID: {existing_upload_id}")
                # Return the existing ID for the frontend to fetch the saved results
                return jsonify({
                    "message": "File content matches a previous analysis. Returning saved results.",
                    "chunks_count": 0, # Skip chunking count since we didn't process
                    "upload_id": existing_upload_id, # Return the EXISTING ID
                    "deduplication_hit": True
                }), 200

            # --- NO DEDUPLICATION HIT: PROCEED WITH AI ANALYSIS ---
            print(f"DEDUPE MISS: File (Hash: {file_hash[:8]}...) requires new analysis.")
            
            # 2. Call the chunking function
            structured_chunks = extract_and_chunk_pdf(temp_filename)
            
            # 3. Call the AI analysis function
            analyzed_tasks = analyze_compliance_chunks(
                structured_chunks=structured_chunks, 
                app_id=__app_id,
                api_key=__api_key
            )
            
            # 4. Save the NEW results (using the current_upload_id)
            save_analyzed_tasks(current_upload_id, file_hash, structured_chunks, analyzed_tasks)
            
            # 5. Return the NEW unique ID
            return jsonify({
                "message": f"AI analysis complete. {len(analyzed_tasks)} tasks identified.",
                "chunks_count": len(structured_chunks),
                "upload_id": current_upload_id, # Return the NEW ID
                "deduplication_hit": False
            }), 200

        except Exception as e:
            print(f"Error during processing for upload_id {current_upload_id}: {e}")
            return jsonify({"error": f"Analysis Failed: Internal server error during PDF processing: {e}"}), 500
        
        finally:
            # 6. Clean up the temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    return jsonify({"error": "Invalid file type. Only PDFs are supported."}), 400

@app.route('/get_latest_tasks/<upload_id>', methods=['GET'])
def get_latest_tasks(upload_id):
    """Endpoint to fetch the analyzed tasks for a specific upload ID."""
    
    tasks = get_latest_analyzed_tasks(upload_id)
    
    if not tasks:
        return jsonify({"message": f"No tasks found for ID {upload_id}."}), 404
    
    return jsonify({
        "analyzed_tasks": tasks,
        "message": f"Successfully retrieved {len(tasks)} compliance tasks.",
        "upload_id": upload_id
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)