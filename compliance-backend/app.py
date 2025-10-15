# app.py
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os

# Local imports
from extract import extract_text_from_pdf   # PDF text extraction
from summarizer import summarize_text       # HuggingFace summarizer
from db import insert_clause, fetch_all_clauses  # SQLite database helpers

app = Flask(__name__)
CORS(app)

# ==== CONFIG ====
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "temp")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ==== ROUTES ====

@app.route("/", methods=["GET"])
def home():
    return jsonify(message="Compliance API running (Flask backend connected to frontend)")

# -------- UPLOAD ROUTE (for PDF) --------
@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify(error="No file part"), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify(error="No selected file"), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        try:
            text = extract_text_from_pdf(file_path)
        except Exception as e:
            return jsonify(error=f"Extraction error: {e}"), 500

        return jsonify(filename=filename, text=text)

    return jsonify(error="Invalid file type"), 400


# -------- SUMMARIZE / CLAUSE EXTRACTION ROUTE --------
@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return jsonify(error="No text provided"), 400

    try:
        summaries = summarize_text(text)
        for summary in summaries:
            insert_clause(summary)  # Save each clause into DB
        return jsonify(summaries=summaries)
    except Exception as e:
        return jsonify(error=f"Summarization failed: {e}"), 500


# -------- FETCH ALL SAVED CLAUSES --------
@app.route("/extract_clauses", methods=["GET"])
def get_clauses():
    try:
        clauses = fetch_all_clauses()
        return jsonify(clauses=clauses)
    except Exception as e:
        return jsonify(error=f"Database fetch failed: {e}"), 500


# ==== MAIN ====
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
