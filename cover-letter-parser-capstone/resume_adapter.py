"""
resume_adapter.py
-----------------
Bridges Alex's resume parser + matcher into Dennis's Flask app.

Dennis's app.py already:
  - extracts the raw text from the upload, and
  - calls  parse_resume(text, job_description)  expecting a result dict.

But Alex's parse_resume(file) takes a FILE PATH and returns a different shape.
This adapter provides a drop-in  parse_resume(text, job_description)  that:
  1. runs Alex's field extractors on the already-extracted text,
  2. runs Alex's matcher against the job description,
  3. returns a dict shaped the way app.py / the resume front-end expect
     (name, email, phone, skills, score, matched/missing, etc.).

USAGE in app.py — change the resume import from:
    from parser import read_document, parse_cover_letter, parse_resume
to keep Dennis's cover-letter parser but use Alex's for resumes:
    from parser import read_document, parse_cover_letter
    from resume_adapter import parse_resume         # Alex's, adapted

Everything else in the /api/parse-resume route stays the same.
"""

import re

# Alex's field extractors (operate on text)
from resume_parser import (
    extract_name, extract_email, extract_phone,
    extract_skills, extract_experience_years,
)
# Alex's matcher
from matcher import match


def _skills_from_job_text(job_description):
    """Turn a pasted job-description string into a required-skills list by
    running Alex's skill extractor over it (same canonical skills as resumes,
    so matched/missing line up)."""
    return extract_skills(job_description or "")


def _guess_min_experience(job_description):
    """Pull a 'N years' minimum from the job text if present, else 0."""
    if not job_description:
        return 0
    m = re.search(r"(\d{1,2})\+?\s*years?", job_description, re.I)
    return int(m.group(1)) if m else 0


def parse_resume(text, job_description=""):
    """Drop-in replacement for Dennis's parse_resume(text, job_description).

    Returns a dict with the keys app.py / resume.js expect.
    """
    # 1) Extract structured fields from the resume text (Alex's extractors)
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)
    experience_years = extract_experience_years(text)

    # 2) Build a job profile from the pasted job description and run the matcher
    required_skills = _skills_from_job_text(job_description)
    job_profile = {
        "title": "Job",
        "required_skills": required_skills,
        "min_experience": _guess_min_experience(job_description),
    }

    parsed_for_match = {
        "parsed": True,
        "file": "",
        "name": name,
        "skills": skills,
        "experience_years": experience_years,
    }

    if required_skills:
        match_result = match(parsed_for_match, job_profile)
        match_score = match_result.get("match_score")
        matched_skills = match_result.get("matched_skills", [])
        missing_skills = match_result.get("missing_skills", [])
        skill_score = match_result.get("skill_score")
        experience_score = match_result.get("experience_score")
    else:
        # No job description pasted -> parse only, no match
        match_score = None
        matched_skills = []
        missing_skills = []
        skill_score = None
        experience_score = None

    # 3) Return a dict shaped for app.py / the resume front-end.
    #    (word_count / sections / summary etc. aren't produced by Alex's
    #     resume pipeline, so they're provided as safe defaults.)
    return {
        "name": name or "Unknown Applicant",
        "email": email,
        "phone": phone,
        "linkedin": None,
        "github": None,
        "skills": skills,
        "experience_years": experience_years,

        # matching results
        "match_percentage": match_score,     # app front-end key for the score
        "score": match_score,
        "matched_keywords": matched_skills,  # matches Dennis's job_match keys
        "missing_keywords": missing_skills,
        "matched_skills": matched_skills,    # also provide Alex-style keys
        "missing_skills": missing_skills,
        "skill_score": skill_score,
        "experience_score": experience_score,

        # fields Dennis's payload/front-end may look for (safe defaults)
        "sections": {},
        "word_count": len((text or "").split()),
        "bullet_count": (text or "").count("\n- ") + (text or "").count("\u2022"),
        "summary": None,
        "rating": None,
        "strengths": [],
        "improvements": [],
    }


# quick manual test
if __name__ == "__main__":
    import json
    sample_resume = (
        "Sarah Mitchell\nsarah@email.com | (415) 555-0182\n"
        "Backend developer with 6 years of experience.\n"
        "Skills: Python, SQL, Docker, AWS, Node.js\n"
    )
    sample_job = "Looking for a backend developer with Python, SQL, Docker. 3+ years experience."
    result = parse_resume(sample_resume, sample_job)
    print(json.dumps(result, indent=2))
