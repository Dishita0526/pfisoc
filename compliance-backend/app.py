# app.py
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
from extract import extract_text_from_pdf  # keep your existing extract.py API

app = Flask(__name__)
CORS(app)  # allow requests from React dev server (localhost:3000)

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "temp")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET"])
def home():
    return jsonify(message="Compliance API running (Flask)")

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

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
