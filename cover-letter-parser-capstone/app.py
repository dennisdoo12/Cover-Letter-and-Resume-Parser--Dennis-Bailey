from pathlib import Path
import uuid

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from parser import read_document, parse_cover_letter, parse_resume


app = Flask(__name__)

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_and_read(uploaded):
    if not uploaded.filename:
        raise ValueError("Please choose a file.")

    if not allowed_file(uploaded.filename):
        raise ValueError("Upload a PDF, DOCX, or TXT file.")

    original_name = secure_filename(uploaded.filename)
    extension = original_name.rsplit(".", 1)[1].lower()

    saved_path = UPLOAD_FOLDER / f"{uuid.uuid4().hex}.{extension}"

    try:
        uploaded.save(saved_path)

        text = read_document(saved_path)

        if not text.strip():
            raise ValueError("No readable text was found.")

        return text, original_name

    finally:
        saved_path.unlink(missing_ok=True)


# --------------------------------------------------
# PAGES
# --------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/resume")
def resume_page():
    return render_template("resume.html")


@app.route("/parsed-text")
def parsed_text_page():
    return render_template("parsed_text.html")


# --------------------------------------------------
# COVER LETTER PARSER
# --------------------------------------------------

@app.route("/api/parse", methods=["POST"])
def parse_cover_letter_file():

    if "cover_letter" not in request.files:
        return jsonify({
            "error": "No cover letter was uploaded."
        }), 400

    uploaded = request.files["cover_letter"]

    job_description = request.form.get(
        "job_description",
        ""
    ).strip()

    try:
        text, original_name = save_and_read(uploaded)

        result = parse_cover_letter(
            text,
            job_description
        )

        result["filename"] = original_name
        result["extracted_text"] = text

        return jsonify(result)

    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    except Exception as exc:
        return jsonify({
            "error": f"Could not parse cover letter: {exc}"
        }), 500


# --------------------------------------------------
# RESUME PARSER
# --------------------------------------------------

@app.route("/api/parse-resume", methods=["POST"])
def parse_resume_file():

    if "resume" not in request.files:
        return jsonify({
            "error": "No resume was uploaded."
        }), 400

    uploaded = request.files["resume"]

    job_description = request.form.get(
        "job_description",
        ""
    ).strip()

    try:
        text, original_name = save_and_read(uploaded)

        result = parse_resume(
            text,
            job_description
        )

        result["filename"] = original_name
        result["extracted_text"] = text

        return jsonify(result)

    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    except Exception as exc:
        return jsonify({
            "error": f"Could not parse resume: {exc}"
        }), 500


@app.errorhandler(413)
def too_large(_):
    return jsonify({
        "error": "Maximum file size is 8 MB."
    }), 413


if __name__ == "__main__":
    app.run(debug=True)