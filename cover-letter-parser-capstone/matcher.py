# Layered scoring. Keyword overlap stays the dominant, explainable signal;
# the semantic layer is a smaller additive boost for meaning keywords miss.
# Set use_semantic=False (default) to run the pure keyword+experience model.
SKILL_WEIGHT = 0.55      # keyword/skill-overlap base layer (explainable)
SEMANTIC_WEIGHT = 0.15   # sentence-transformer similarity (ML layer)
EXP_WEIGHT = 0.30


def score_skills(candidate_skills, required_skills):
    #  Case-normalize so "Python" == "python".
    required = {s.lower(): s for s in required_skills}   
    candidate = {s.lower() for s in candidate_skills}

    matched = [orig for low, orig in required.items() if low in candidate]
    missing = [orig for low, orig in required.items() if low not in candidate]

    if not required:
        score = 1.0            # no requirements everyone matches
    else:
        score = len(matched) / len(required)

    return {
        "score": score,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
    }


def score_experience(candidate_years, minimum_years):
    if not minimum_years:          # no minimum specified 
        return 1.0
    if candidate_years is None:    # couldn't extract experience 
        return 0.0
    if candidate_years >= minimum_years:
        return 1.0
    # below minimum: partial credit proportional to how close they are
    return round(candidate_years / minimum_years, 2)


def match(parsed_resume, job_profile, resume_text=None, use_semantic=False,
          embed_fn=None):
    # If the resume couldn't be parsed, it can't be scored.
    if not parsed_resume.get("parsed", False):
        return {
            "scored": False,
            "reason": "Resume could not be parsed.",
            "file": parsed_resume.get("file"),
        }

    candidate_skills = parsed_resume.get("skills", [])
    candidate_years = parsed_resume.get("experience_years")

    required_skills = job_profile.get("required_skills", [])
    min_experience = job_profile.get("min_experience", 0)

    skills_result = score_skills(candidate_skills, required_skills)
    exp_score = score_experience(candidate_years, min_experience)

    # If sentence-transformers isn't installed fall back to keyword-only
    sem_result = None
    if use_semantic and resume_text:
        try:
            from semantic_matcher import semantic_score
            sem_result = semantic_score(resume_text, required_skills,
                                        embed_fn=embed_fn)
            sem_score = sem_result["semantic_score"]
            final = (SKILL_WEIGHT * skills_result["score"]
                     + SEMANTIC_WEIGHT * sem_score
                     + EXP_WEIGHT * exp_score)
        except Exception:
            sem_result = None
            kw_weight = SKILL_WEIGHT + SEMANTIC_WEIGHT
            final = (kw_weight * skills_result["score"]) + (EXP_WEIGHT * exp_score)
    else:
        # No semantic layer
        kw_weight = SKILL_WEIGHT + SEMANTIC_WEIGHT
        final = (kw_weight * skills_result["score"]) + (EXP_WEIGHT * exp_score)

    out = {
        "scored": True,
        "file": parsed_resume.get("file"),
        "name": parsed_resume.get("name"),
        # final score as a 0-100 number, rounded, for the ranked table
        "match_score": round(final * 100),
        "skill_score": round(skills_result["score"] * 100),
        "experience_score": round(exp_score * 100),
        "matched_skills": skills_result["matched_skills"],
        "missing_skills": skills_result["missing_skills"],
        "candidate_experience_years": candidate_years,
    }
    if sem_result is not None:
        out["semantic_score"] = round(sem_result["semantic_score"] * 100)
        out["semantic_hits"] = sem_result["semantic_hits"]
    return out


def rank_candidates(parsed_resumes, job_profile, use_semantic=True,
                    resume_texts=None, embed_fn=None):
    # resume_texts: optional dict {file -> raw resume text} for the semantic
    # layer. Falls back to a "text" key on the parsed dict if present.
    resume_texts = resume_texts or {}

    def _text_for(r):
        return resume_texts.get(r.get("file")) or r.get("text")

    results = [
        match(r, job_profile, resume_text=_text_for(r),
              use_semantic=use_semantic, embed_fn=embed_fn)
        for r in parsed_resumes
    ]

    # sort scored candidates by score descending;
    results.sort(
        key=lambda r: r["match_score"] if r.get("scored") else -1,
        reverse=True,
    )
    return results


# manual test
if __name__ == "__main__":
    import json

    job = {
        "title": "Backend Developer",
        "required_skills": ["Python", "SQL", "React", "Docker"],
        "min_experience": 3,
    }

    # simulate parsed resumes (as parse_resume would return)
    candidates = [
        {
            "parsed": True, "file": "alice.pdf", "name": "Alice Chen",
            "skills": ["Python", "SQL", "React", "Docker", "AWS"],
            "experience_years": 5,
        },
        {
            "parsed": True, "file": "bob.pdf", "name": "Bob Ray",
            "skills": ["Python", "SQL"],
            "experience_years": 2,
        },
        {
            "parsed": True, "file": "carol.pdf", "name": "Carol Diaz",
            "skills": ["Python", "React", "Docker"],
            "experience_years": 4,
        },
        {
            "parsed": False, "file": "scanned.pdf",
            "reason": "No extractable text.",
        },
    ]

    ranked = rank_candidates(candidates, job)
    print(json.dumps(ranked, indent=2))
