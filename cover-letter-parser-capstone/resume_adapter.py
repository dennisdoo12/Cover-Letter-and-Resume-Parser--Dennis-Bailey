"""
resume_adapter.py
-----------------
Connects Alex's resume parser + matcher to Dennis's Flask resume UI.

Dennis's app.py sends this adapter:
- already-extracted resume text
- pasted job description text

This adapter returns a result dict that the UI can display and that Bayram's
backend can save as ranking data.
"""

import re

from resume_parser import (
    extract_name,
    extract_email,
    extract_phone,
    extract_skills,
    extract_experience_years,
)

from matcher import match


def _skills_from_job_text(job_description):
    return extract_skills(job_description or "")


def _guess_min_experience(job_description):
    if not job_description:
        return 0

    match_years = re.search(r"(\d{1,2})\+?\s*years?", job_description, re.I)

    if match_years:
        return int(match_years.group(1))

    return 0


def _detect_sections(text):
    section_names = [
        "Summary",
        "Experience",
        "Education",
        "Skills",
        "Projects",
        "Certifications",
    ]

    found = {}

    lowered_lines = [
        line.strip().lower()
        for line in (text or "").splitlines()
        if line.strip()
    ]

    for section in section_names:
        section_lower = section.lower()

        found[section] = any(
            line == section_lower
            or line.startswith(section_lower + ":")
            for line in lowered_lines
        )

    return found


def _simple_summary(text):
    """Build a clean summary of the resume.

    Prefers the resume's own SUMMARY / OBJECTIVE / PROFILE section if it has
    one. Otherwise falls back to the first couple of sentences. Truncates on a
    sentence boundary (not mid-word) so it doesn't cut off awkwardly.
    """
    if not text:
        return None

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # 1) Try to grab the resume's own summary-type section
    section_headers = ("summary", "objective", "profile", "about")
    for i, line in enumerate(lines):
        low = line.lower().rstrip(":")
        if low in section_headers:
            # collect lines after the header until the next ALL-CAPS/section-like line
            collected = []
            for nxt in lines[i + 1:]:
                # stop at the next section header (short all-caps line)
                if nxt.isupper() and len(nxt.split()) <= 4:
                    break
                collected.append(nxt)
                if len(" ".join(collected)) > 300:
                    break
            if collected:
                summary = " ".join(collected)
                return _truncate_on_sentence(summary, 300)

    # 2) Fallback: first few sentences of the whole resume
    clean_text = " ".join(text.split())
    return _truncate_on_sentence(clean_text, 300)


def _truncate_on_sentence(s, limit):
    """Cut a string near `limit` chars, but on a sentence/word boundary so it
    doesn't end mid-word."""
    if len(s) <= limit:
        return s
    cut = s[:limit]
    # prefer to end at the last sentence end
    last_period = cut.rfind(". ")
    if last_period > limit * 0.5:
        return cut[:last_period + 1]
    # otherwise end at the last full word
    last_space = cut.rfind(" ")
    if last_space > 0:
        return cut[:last_space] + "..."
    return cut + "..."


def _rating_from_score(score):
    if score is None:
        return None

    if score >= 85:
        return "Strong"

    if score >= 70:
        return "Good"

    if score >= 50:
        return "Average"

    return "Needs Improvement"


def _build_strengths(skills, matched_skills, sections, score):
    strengths = []

    if skills:
        strengths.append("Resume includes detected technical skills.")

    if matched_skills:
        strengths.append("Resume matches some required job skills.")

    if sections.get("Experience"):
        strengths.append("Resume includes an Experience section.")

    if sections.get("Education"):
        strengths.append("Resume includes an Education section.")

    if score is not None and score >= 80:
        strengths.append("Resume has strong alignment with the job description.")

    return strengths


def _build_improvements(missing_skills, sections, experience_years):
    improvements = []

    if missing_skills:
        improvements.append(
            "Add or highlight missing job skills: "
            + ", ".join(missing_skills)
            + "."
        )

    if not sections.get("Experience"):
        improvements.append("Add a clear Experience section.")

    if not sections.get("Education"):
        improvements.append("Add a clear Education section.")

    if experience_years is None:
        improvements.append("Include years of experience more clearly if possible.")

    return improvements


def parse_resume(text, job_description=""):
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)
    experience_years = extract_experience_years(text)

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
        semantic = match_result.get("semantic_score")  # present only if semantic on

        # Build the Score Breakdown from the real matcher sub-scores.
        # These explain WHY the match score is what it is.
        category_scores = {
            "Skill Match": skill_score if skill_score is not None else 0,
            "Experience Match": experience_score if experience_score is not None else 0,
        }
        if semantic is not None:
            category_scores["Semantic Match"] = semantic
    else:
        # No job description pasted -> we didn't attempt a match.
        # Use None (not 0) so the UI can show "no job description" rather than
        # a misleading 0/100 that makes the resume look like it failed.
        match_score = None
        matched_skills = []
        missing_skills = []
        skill_score = None
        experience_score = None
        category_scores = {}

    sections = _detect_sections(text)
    summary = _simple_summary(text)
    rating = _rating_from_score(match_score)

    strengths = _build_strengths(
        skills,
        matched_skills,
        sections,
        match_score,
    )

    improvements = _build_improvements(
        missing_skills,
        sections,
        experience_years,
    )

    return {
        "name": name or "Unknown Applicant",
        "email": email,
        "phone": phone,
        "linkedin": None,
        "github": None,

        "skills": skills,
        "experience_years": experience_years,

        "match_percentage": match_score,
        "score": match_score,
        "matched_keywords": matched_skills,
        "missing_keywords": missing_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_score": skill_score,
        "experience_score": experience_score,
        "category_scores": category_scores,

        "sections": sections,
        "word_count": len((text or "").split()),
        "bullet_count": (text or "").count("\n- ") + (text or "").count("\u2022"),
        "summary": summary,
        "rating": rating,
        "strengths": strengths,
        "improvements": improvements,
    }


if __name__ == "__main__":
    import json

    sample_resume = (
        "Sarah Mitchell\nsarah@email.com | (415) 555-0182\n"
        "SUMMARY\n"
        "Backend developer with 6 years of experience.\n"
        "SKILLS\n"
        "Python, SQL, Docker, AWS, Node.js\n"
        "EXPERIENCE\n"
        "Built backend APIs.\n"
        "EDUCATION\n"
        "Computer Science Student\n"
    )

    sample_job = (
        "Looking for a backend developer with Python, SQL, Docker. "
        "3+ years experience."
    )

    result = parse_resume(sample_resume, sample_job)
    print(json.dumps(result, indent=2))