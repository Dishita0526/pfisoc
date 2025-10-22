import os
import json
import tempfile
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS

from extract import extract_and_chunk_pdf 
from ai_parser import analyze_compliance_chunks 
# Placeholder for Phase 3: from db_manager import initialize_db, save_regulatory_chunks, save_analyzed_tasks

from dotenv import load_dotenv
load_dotenv()  # <-- loads variables from .env into os.environ

# --- Global Environment Variables (MUST be present for Firestore access) ---
# NOTE: These variables are provided by the canvas environment at runtime.

print("DEBUG: GEMINI_API_KEY =", os.environ.get("GEMINI_API_KEY"))

__app_id = os.environ.get('APP_ID', 'default-app-id')
__firebase_config = os.environ.get('FIREBASE_CONFIG', '{}')

__api_key = os.environ.get('GEMINI_API_KEY', '')
print("DEBUG: Loaded API key (len):", len(__api_key))
    
# --- Configuration ---
app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir() # Use system temp folder for storage

@app.route('/', methods=['GET'])
def home():
    """Simple status check for the backend."""
    return "Compliance Backend Running Successfully!"

@app.route('/upload_regulation', methods=['POST'])
def upload_regulation():
    """
    Handles PDF upload, chunks the document, and runs AI analysis.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400
    
    if file and file.filename.endswith('.pdf'):
        temp_dir = app.config['UPLOAD_FOLDER']
        temp_filename = os.path.join(temp_dir, str(uuid.uuid4()) + file.filename)
        
        try:
            # 1. Save the file temporarily
            file.save(temp_filename)

            # 2. Call the chunking function
            structured_chunks = extract_and_chunk_pdf(temp_filename)
            
            # 3. Call the AI analysis function, PASSING THE API KEY
            analyzed_tasks = analyze_compliance_chunks(
                structured_chunks=structured_chunks, 
                app_id=__app_id,
                api_key=__api_key  # CRITICAL: Pass the key here
            )
            
            # 4. Phase 2 Return (for validation only - will be replaced in Phase 3)
            return jsonify({
                "message": f"AI analysis complete. **{len(analyzed_tasks)}** compliance tasks identified.",
                "chunks_count": len(structured_chunks),
                "analyzed_tasks": analyzed_tasks,
            }), 200

        except Exception as e:
            print(f"Error during processing: {e}")
            return jsonify({"error": f"Analysis Failed: Internal server error during PDF processing: {e}"}), 500
        
        finally:
            # 5. Clean up the temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    return jsonify({"error": "Invalid file type. Only PDFs are supported."}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
