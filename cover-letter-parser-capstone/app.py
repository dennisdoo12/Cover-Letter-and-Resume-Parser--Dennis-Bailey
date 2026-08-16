from pathlib import Path
import uuid
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename
from parser import read_document, parse_cover_letter
#flask is simple python web framework used to build websites
#basically a Flask web application that allows users to upload cover letters in various formats (PDF, DOCX, TXT), extracts relevant information from the cover letter, and evaluates its quality based on predefined criteria. The application provides an API endpoint for parsing the uploaded cover letter and returns the extracted information in JSON format. It also includes error handling for file uploads and size limits.
app = Flask(__name__)
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/parsed-text")
def parsed_text_page():
    return render_template("parsed_text.html")

@app.route("/api/parse", methods=["POST"])
def parse_file():
    if "cover_letter" not in request.files:
        return jsonify({"error": "No cover letter was uploaded."}), 400

    uploaded = request.files["cover_letter"]
    job_description = request.form.get("job_description", "").strip()

    if not uploaded.filename:
        return jsonify({"error": "Please choose a file."}), 400
    if not allowed_file(uploaded.filename):
        return jsonify({"error": "Upload a PDF, DOCX, or TXT file."}), 400

    original_name = secure_filename(uploaded.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    saved_path = UPLOAD_FOLDER / f"{uuid.uuid4().hex}.{extension}"

    try:
        uploaded.save(saved_path)
        text = read_document(saved_path)
        if not text.strip():
            return jsonify({"error": "No readable text was found."}), 400

        result = parse_cover_letter(text, job_description)
        result["filename"] = original_name
        result["extracted_text"] = text
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": f"Could not parse cover letter: {exc}"}), 500
    finally:
        saved_path.unlink(missing_ok=True)

@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "Maximum file size is 8 MB."}), 413

if __name__ == "__main__":
    app.run(debug=True)
