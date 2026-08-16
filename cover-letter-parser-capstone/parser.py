import re
from pathlib import Path
from docx import Document
from pypdf import PdfReader
#common skills dictionary for cover letter parsing
COMMON_SKILLS = [
    "Python", "JavaScript", "React", "Node.js", "SQL", "PostgreSQL", "MySQL",
    "Git", "GitHub", "HTML", "CSS", "Java", "C++", "C#", "AWS", "Azure",
    "Docker", "Kubernetes", "Microsoft Excel", "Power BI", "Tableau",
    "Snowflake", "Flask", "Django", "FastAPI", "REST API", "Linux",
    "Windows", "Jira", "Project Management", "Communication", "Leadership",
    "Data Analysis", "Customer Service", "Marketing"
]

ACTION_VERBS = [
    "achieved", "built", "created", "developed", "designed", "implemented",
    "improved", "increased", "led", "managed", "organized", "reduced",
    "resolved", "supported", "collaborated", "analyzed", "delivered",
    "launched", "automated", "coordinated", "optimized", "generated"
]
#reads the document based on the file type and returns the text content
def read_document(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".txt":
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        return "\n".join((p.extract_text() or "").strip() for p in PdfReader(path).pages)
    if suffix == ".docx":
        doc = Document(path)
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        parts.append(cell.text.strip())
        return "\n".join(parts)
    raise ValueError("Unsupported file type.")
#extracts the first match of a regex pattern from the text, ignoring case
def extract(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0).strip() if match else None
#extracts the applicant's name from the cover letter text, ignoring common greetings and invalid lines
def extract_name(text):
    ignored = {"dear hiring manager", "dear recruiter", "to whom it may concern"}
    for line in [x.strip() for x in text.splitlines() if x.strip()][:8]:
        low = line.lower().strip(" ,:")
        if low in ignored or "@" in line or re.search(r"\d", line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(re.fullmatch(r"[A-Za-z.'-]+", w) for w in words):
            return line
    return None
#extracts common skills from the cover letter text by matching against a predefined list of skills
def extract_skills(text):
    return [s for s in COMMON_SKILLS if re.search(rf"(?<!\w){re.escape(s)}(?!\w)", text, re.I)]

def count_words(text):
    return len(re.findall(r"\b[\w+#.-]+\b", text))

def summarize(text, max_chars=420):
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rsplit(" ", 1)[0] + "..."

def job_match(text, job_description):
    if not job_description.strip():
        return {"matched_keywords": [], "match_percentage": None}
    stop = {"the","and","for","with","that","this","from","your","our","you","are","will","job","role","position","candidate","experience","skills","work","team","company"}
    job_words = {w for w in re.findall(r"\b[a-zA-Z][a-zA-Z+#.-]{2,}\b", job_description.lower()) if w not in stop}
    text_words = set(re.findall(r"\b[a-zA-Z][a-zA-Z+#.-]{2,}\b", text.lower()))
    matched = sorted(job_words & text_words)
    pct = round(len(matched) / len(job_words) * 100) if job_words else 0
    return {"matched_keywords": matched[:25], "match_percentage": pct}
#main parse cover letter function that extracts various elements from the cover letter text and evaluates its quality based on predefined criteria. various metrics
def parse_cover_letter(text, job_description=""):
    email = extract(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    phone = extract(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}", text)
    linkedin = extract(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+/?", text)
    name = extract_name(text)
    skills = extract_skills(text)
    words = count_words(text)
    sentences = max(1, len([s for s in re.split(r"[.!?]+", text) if s.strip()]))
    avg_sentence = words / sentences
    greeting = bool(re.search(r"(?mi)^\s*(dear .+|to whom it may concern)[,:\s]*$", text))
    closing = bool(re.search(r"(?mi)^\s*(sincerely|regards|best regards|thank you|respectfully)[,:\s]*$", text))
    interest = bool(re.search(r"\b(apply(?:ing)? for|interested in|excited to apply|position|role)\b", text, re.I))
    company = bool(re.search(r"\bat [A-Z][A-Za-z0-9&.' -]{2,}\b", text))
    actions = [v for v in ACTION_VERBS if re.search(rf"\b{v}\b", text, re.I)]
    metrics = re.findall(r"\b\d+(?:\.\d+)?%\b|\$\s?\d[\d,]*|\b\d[\d,]*\+\b", text)
    match = job_match(text, job_description)

    scores = {}
    scores["Contact Information"] = (3 if name else 0) + (3 if email else 0) + (2 if phone else 0) + (2 if linkedin else 0)
    scores["Professional Structure"] = (5 if greeting else 0) + (5 if closing else 0) + (5 if sentences >= 3 else 0)
    relevance = (8 if interest else 0) + (6 if company else 0)
    if match["match_percentage"] is not None:
        relevance += 6 if match["match_percentage"] >= 30 else 4 if match["match_percentage"] >= 15 else 2 if match["match_percentage"] > 0 else 0
    elif skills:
        relevance += 4
    scores["Job Relevance"] = min(relevance, 20)

    skill_score = min(len(skills) * 3, 12) + (4 if len(actions) >= 4 else 2 if len(actions) >= 2 else 0) + (4 if len(metrics) >= 2 else 2 if len(metrics) == 1 else 0)
    scores["Skills and Qualifications"] = min(skill_score, 20)
    clarity = (6 if 180 <= words <= 500 else 4 if 120 <= words <= 650 else 0) + (5 if avg_sentence <= 24 else 3 if avg_sentence <= 30 else 0)
    if not re.search(r"\b(stuff|whatever|probably|kinda|sort of)\b", text, re.I):
        clarity += 4
    scores["Writing Clarity"] = min(clarity, 15)
    scores["Personalization"] = min((5 if company else 0) + (3 if re.search(r"\b(because|particularly|specifically)\b", text, re.I) else 0) + (2 if "your company" not in text.lower() else 0), 10)
    scores["Completeness"] = min((4 if words >= 150 else 0) + (2 if greeting else 0) + (2 if closing else 0) + (2 if interest else 0), 10)

    total = max(1, min(sum(scores.values()), 100))
    rating = "Excellent" if total >= 85 else "Strong" if total >= 70 else "Average" if total >= 55 else "Needs Improvement" if total >= 40 else "Weak"

    strengths, improvements = [], []
    checks = [
        (scores["Contact Information"] >= 8, "Includes clear applicant contact information.", "Add your full name, email, phone number, and LinkedIn profile."),
        (scores["Professional Structure"] >= 12, "Uses a clear professional cover letter structure.", "Include a professional greeting, body paragraphs, and closing."),
        (scores["Job Relevance"] >= 15, "Connects the applicant's background to the target role.", "Explain why you want this role and connect experience to requirements."),
        (scores["Skills and Qualifications"] >= 14, "Provides strong evidence of relevant skills and qualifications.", "Add more relevant skills, accomplishments, and measurable results."),
        (scores["Writing Clarity"] >= 12, "Writing is concise, professional, and easy to read.", "Use clearer wording, shorter sentences, and a professional tone."),
        (scores["Personalization"] >= 7, "The letter appears tailored to the employer.", "Mention the employer by name and explain why it interests you."),
        (scores["Completeness"] >= 8, "Includes the major expected cover letter components.", "Add a clear introduction, qualifications, employer connection, and closing.")
    ]
    for passed, good, fix in checks:
        (strengths if passed else improvements).append(good if passed else fix)

    return {
        "name": name, "email": email, "phone": phone, "linkedin": linkedin,
        "skills": skills, "word_count": words, "summary": summarize(text),
        "score": total, "rating": rating, "category_scores": scores,
        "strengths": strengths, "improvements": improvements,
        "action_verbs": actions, "metrics": metrics,
        "readability": {"sentence_count": sentences, "average_sentence_length": round(avg_sentence, 1)},
        "job_match": match
    }
