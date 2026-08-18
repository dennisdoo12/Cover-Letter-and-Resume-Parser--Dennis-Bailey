from pathlib import Path
import uuid
import requests

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

# Dennis cover letter parser and file reader
from parser import read_document, parse_cover_letter

# Alex resume parser/matcher adapter
from resume_adapter import parse_resume


app = Flask(__name__)

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

BACKEND_URL = "http://localhost:5050"


def normalize_skills(skills):
    if not skills:
        return []

    if isinstance(skills, list):
        return skills

    if isinstance(skills, str):
        return [
            skill.strip()
            for skill in skills.split(",")
            if skill.strip()
        ]

    return []


def login_to_backend():
    login_response = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={
            "username": "dummyUser",
            "password": "SecretPassWord1223"
        },
        timeout=10
    )

    token = login_response.json().get("token")

    if not token:
        print("Backend login failed:", login_response.text)
        return None

    return token


def build_cover_letter_payload(result, original_name):
    skills = normalize_skills(result.get("skills"))

    return {
        "file": original_name,
        "filename": original_name,
        "document_type": "cover_letter",

        "name": result.get("name") or result.get("applicant_name") or "Unknown Applicant",
        "email": result.get("email"),
        "phone": result.get("phone"),
        "linkedin": result.get("linkedin"),
        "github": result.get("github"),

        "skills": skills,
        "sections": result.get("sections") or result.get("sections_found", {}),
        "word_count": result.get("word_count"),
        "bullet_count": result.get("bullet_count"),
        "summary": result.get("summary"),
        "score": result.get("score") or result.get("quality_score"),
        "rating": result.get("rating"),
        "strengths": result.get("strengths", []),
        "improvements": result.get("improvements", []),
        "extracted_text": result.get("extracted_text", ""),

        "full_parser_output": result
    }


def build_resume_payload(result, original_name):
    skills = normalize_skills(result.get("skills"))

    return {
        "parsed": True,
        "scored": True,
        "file": original_name,

        "name": result.get("name") or result.get("applicant_name") or "Unknown Applicant",
        "email": result.get("email"),
        "phone": result.get("phone"),

        "skills": skills,
        "experience_years": (
            result.get("experience_years")
            or result.get("years_experience")
            or 0
        ),

        "jobId": 1,

        "match_score": (
            result.get("match_percentage")
            or result.get("match_score")
            or result.get("score")
            or result.get("quality_score")
            or 0
        ),

        "matched_skills": (
            result.get("matched_skills")
            or result.get("matched_keywords")
            or []
        ),

        "missing_skills": (
            result.get("missing_skills")
            or result.get("missing_keywords")
            or []
        ),

        "candidate_experience_years": (
            result.get("experience_years")
            or result.get("years_experience")
            or 0
        )
    }


def send_cover_letter_to_backend(payload):
    try:
        token = login_to_backend()

        if not token:
            return None

        backend_response = requests.post(
            f"{BACKEND_URL}/api/cover-letter-results",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=10
        )

        print("Cover letter backend status:", backend_response.status_code)
        print("Cover letter backend response:", backend_response.text)

        return backend_response

    except Exception as exc:
        print("Could not send cover letter result to backend:", exc)
        return None


def send_resume_to_backend(payload):
    try:
        token = login_to_backend()

        if not token:
            return None

        backend_response = requests.post(
            f"{BACKEND_URL}/api/parser-results",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=10
        )

        print("Resume backend status:", backend_response.status_code)
        print("Resume backend response:", backend_response.text)

        return backend_response

    except Exception as exc:
        print("Could not send resume result to backend:", exc)
        return None


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

        backend_payload = build_cover_letter_payload(
            result,
            original_name
        )

        send_cover_letter_to_backend(backend_payload)

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

        backend_payload = build_resume_payload(
            result,
            original_name
        )

        send_resume_to_backend(backend_payload)

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