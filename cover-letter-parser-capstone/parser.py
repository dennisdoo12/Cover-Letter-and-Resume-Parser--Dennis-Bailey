import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader


# --------------------------------------------------
# SKILL DATABASE
# --------------------------------------------------

COMMON_SKILLS = [

    # Programming
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "C++",
    "C#",
    "C",
    "Go",
    "Rust",
    "Ruby",
    "PHP",
    "Swift",
    "Kotlin",
    "R",
    "MATLAB",
    "Bash",
    "PowerShell",

    # Web Development
    "HTML",
    "CSS",
    "React",
    "Angular",
    "Vue",
    "Next.js",
    "Node.js",
    "Express",
    "Flask",
    "Django",
    "FastAPI",
    "REST API",
    "GraphQL",

    # Databases / Data
    "SQL",
    "PostgreSQL",
    "MySQL",
    "SQLite",
    "MongoDB",
    "Redis",
    "Snowflake",
    "Oracle",
    "Microsoft SQL Server",
    "ETL",
    "Data Analysis",
    "Data Visualization",
    "Data Modeling",
    "Machine Learning",
    "Deep Learning",
    "Natural Language Processing",
    "NLP",
    "Computer Vision",
    "Pandas",
    "NumPy",
    "Scikit-learn",
    "TensorFlow",
    "PyTorch",
    "Power BI",
    "Tableau",
    "Microsoft Excel",

    # Cloud / DevOps
    "AWS",
    "Azure",
    "Google Cloud",
    "GCP",
    "Docker",
    "Kubernetes",
    "Terraform",
    "Ansible",
    "Jenkins",
    "GitHub Actions",
    "CI/CD",

    # IT / Infrastructure
    "Linux",
    "Windows",
    "Windows Server",
    "Active Directory",
    "Microsoft 365",
    "Intune",
    "VMware",
    "Networking",
    "TCP/IP",
    "DNS",
    "DHCP",
    "VPN",
    "Firewalls",

    # Cybersecurity
    "Cybersecurity",
    "Information Security",
    "SIEM",
    "SOC",
    "EDR",
    "Endpoint Security",
    "Vulnerability Management",
    "Incident Response",
    "Identity and Access Management",
    "IAM",

    # Development Tools
    "Git",
    "GitHub",
    "GitLab",
    "Jira",
    "Confluence",
    "Agile",
    "Scrum",
    "Software Development",
    "Software Testing",
    "Unit Testing",
    "API Testing",
    "Debugging",
    "Troubleshooting",

    # IT Support
    "Technical Support",
    "IT Support",
    "Help Desk",
    "Service Desk",
    "Hardware Support",
    "Software Support",
    "Ticketing Systems",
    "Remote Support",
    "System Administration",
    "Network Administration",

    # Business
    "Project Management",
    "Product Management",
    "Risk Management",
    "Stakeholder Management",
    "Business Analysis",
    "Requirements Gathering",
    "Process Improvement",
    "Quality Assurance",
    "Documentation",
    "Training",
    "Customer Service",
    "Sales",
    "Marketing",
    "Digital Marketing",
    "Social Media",
    "SEO",
    "SEM",
    "Google Analytics",

    # Creative
    "Adobe Photoshop",
    "Adobe Premiere Pro",
    "Adobe Illustrator",
    "Figma",
    "Canva",
    "Video Editing",
    "Graphic Design",
    "WordPress",
    "Mailchimp",

    # Professional Skills
    "Communication",
    "Leadership",
    "Teamwork",
    "Collaboration",
    "Problem Solving",
    "Critical Thinking",
    "Time Management",
    "Organization",
    "Research",
    "Presentation",
    "Writing"
]


ACTION_VERBS = [
    "achieved",
    "administered",
    "analyzed",
    "automated",
    "built",
    "collaborated",
    "configured",
    "coordinated",
    "created",
    "delivered",
    "deployed",
    "designed",
    "developed",
    "diagnosed",
    "directed",
    "engineered",
    "generated",
    "implemented",
    "improved",
    "increased",
    "installed",
    "launched",
    "led",
    "maintained",
    "managed",
    "migrated",
    "monitored",
    "optimized",
    "organized",
    "produced",
    "reduced",
    "resolved",
    "supported",
    "tested",
    "trained",
    "troubleshot",
    "upgraded"
]


STOP_WORDS = {
    "the", "and", "for", "with", "that", "this",
    "from", "your", "our", "you", "are", "will",
    "job", "role", "position", "candidate",
    "experience", "skills", "work", "team",
    "company", "have", "has", "who", "but",
    "not", "all", "can", "their", "they",
    "its", "into", "about", "years", "year",
    "required", "preferred", "responsibilities",
    "requirements", "including", "using"
}


# --------------------------------------------------
# DOCUMENT READING
# --------------------------------------------------

def read_document(path):

    suffix = Path(path).suffix.lower()

    if suffix == ".txt":
        return Path(path).read_text(
            encoding="utf-8",
            errors="ignore"
        )

    if suffix == ".pdf":
        return "\n".join(
            (page.extract_text() or "").strip()
            for page in PdfReader(path).pages
        )

    if suffix == ".docx":

        doc = Document(path)

        parts = [
            p.text.strip()
            for p in doc.paragraphs
            if p.text.strip()
        ]

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:

                    if cell.text.strip():
                        parts.append(
                            cell.text.strip()
                        )

        return "\n".join(parts)

    raise ValueError("Unsupported file type.")


# --------------------------------------------------
# BASIC EXTRACTION
# --------------------------------------------------

def extract(pattern, text):

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    return match.group(0).strip() if match else None


def extract_name(text):

    ignored = {
        "dear hiring manager",
        "dear recruiter",
        "to whom it may concern",
        "professional summary",
        "summary",
        "resume",
        "curriculum vitae"
    }

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ][:10]

    for line in lines:

        low = line.lower().strip(" ,:")

        if (
            low in ignored
            or "@" in line
            or re.search(r"\d", line)
        ):
            continue

        words = line.split()

        if (
            2 <= len(words) <= 4
            and all(
                re.fullmatch(
                    r"[A-Za-z.'-]+",
                    word
                )
                for word in words
            )
        ):
            return line

    return None


def extract_skills(text):

    found = []

    for skill in COMMON_SKILLS:

        if re.search(
            rf"(?<!\w){re.escape(skill)}(?!\w)",
            text,
            re.I
        ):
            found.append(skill)

    return found


def count_words(text):

    return len(
        re.findall(
            r"\b[\w+#.-]+\b",
            text
        )
    )


def summarize(text, max_chars=420):

    clean = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    if len(clean) <= max_chars:
        return clean

    return (
        clean[:max_chars]
        .rsplit(" ", 1)[0]
        + "..."
    )


# --------------------------------------------------
# JOB DESCRIPTION MATCHING
# --------------------------------------------------

def job_match(text, job_description):

    if not job_description.strip():

        return {
            "matched_keywords": [],
            "missing_keywords": [],
            "match_percentage": None
        }

    job_words = {
        word
        for word in re.findall(
            r"\b[a-zA-Z][a-zA-Z+#.-]{2,}\b",
            job_description.lower()
        )
        if word not in STOP_WORDS
    }

    text_words = set(
        re.findall(
            r"\b[a-zA-Z][a-zA-Z+#.-]{2,}\b",
            text.lower()
        )
    )

    matched = sorted(
        job_words & text_words
    )

    missing = sorted(
        job_words - text_words
    )

    percentage = (
        round(
            len(matched)
            / len(job_words)
            * 100
        )
        if job_words
        else 0
    )

    return {
        "matched_keywords": matched[:30],
        "missing_keywords": missing[:30],
        "match_percentage": percentage
    }


# --------------------------------------------------
# SHARED INFORMATION
# --------------------------------------------------

def extract_common_details(text):

    email = extract(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text
    )

    phone = extract(
        r"(?:\+?1[-.\s]?)?"
        r"(?:\(?\d{3}\)?[-.\s]?)"
        r"\d{3}[-.\s]?\d{4}",
        text
    )

    linkedin = extract(
        r"(?:https?://)?"
        r"(?:www\.)?"
        r"linkedin\.com/in/"
        r"[A-Za-z0-9_-]+/?",
        text
    )

    name = extract_name(text)

    skills = extract_skills(text)

    actions = [
        verb
        for verb in ACTION_VERBS
        if re.search(
            rf"\b{verb}\b",
            text,
            re.I
        )
    ]

    metrics = re.findall(
        r"\b\d+(?:\.\d+)?%\b"
        r"|\$\s?\d[\d,]*(?:\.\d+)?"
        r"|\b\d[\d,]*\+\b",
        text
    )

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "skills": skills,
        "action_verbs": actions,
        "metrics": metrics
    }


# --------------------------------------------------
# COVER LETTER PARSER
# --------------------------------------------------

def parse_cover_letter(
    text,
    job_description=""
):

    details = extract_common_details(text)

    name = details["name"]
    email = details["email"]
    phone = details["phone"]
    linkedin = details["linkedin"]

    skills = details["skills"]
    actions = details["action_verbs"]
    metrics = details["metrics"]

    words = count_words(text)

    sentences = max(
        1,
        len([
            sentence
            for sentence in re.split(
                r"[.!?]+",
                text
            )
            if sentence.strip()
        ])
    )

    avg_sentence = words / sentences

    greeting = bool(
        re.search(
            r"(?mi)^\s*"
            r"(dear .+|to whom it may concern)"
            r"[,:\s]*$",
            text
        )
    )

    closing = bool(
        re.search(
            r"(?mi)^\s*"
            r"(sincerely|regards|best regards|thank you|respectfully)"
            r"[,:\s]*$",
            text
        )
    )

    interest = bool(
        re.search(
            r"\b("
            r"apply(?:ing)? for"
            r"|interested in"
            r"|excited to apply"
            r"|position"
            r"|role"
            r")\b",
            text,
            re.I
        )
    )

    company = bool(
        re.search(
            r"\bat [A-Z][A-Za-z0-9&.' -]{2,}\b",
            text
        )
    )

    match = job_match(
        text,
        job_description
    )

    scores = {}

    scores["Contact Information"] = (
        (3 if name else 0)
        + (3 if email else 0)
        + (2 if phone else 0)
        + (2 if linkedin else 0)
    )

    scores["Professional Structure"] = (
        (5 if greeting else 0)
        + (5 if closing else 0)
        + (5 if sentences >= 3 else 0)
    )

    relevance = (
        (8 if interest else 0)
        + (6 if company else 0)
    )

    if match["match_percentage"] is not None:

        if match["match_percentage"] >= 30:
            relevance += 6

        elif match["match_percentage"] >= 15:
            relevance += 4

        elif match["match_percentage"] > 0:
            relevance += 2

    elif skills:
        relevance += 4

    scores["Job Relevance"] = min(
        relevance,
        20
    )

    skill_score = (
        min(len(skills) * 3, 12)
        + (
            4 if len(actions) >= 4
            else 2 if len(actions) >= 2
            else 0
        )
        + (
            4 if len(metrics) >= 2
            else 2 if len(metrics) == 1
            else 0
        )
    )

    scores["Skills and Qualifications"] = min(
        skill_score,
        20
    )

    clarity = (
        (
            6 if 180 <= words <= 500
            else 4 if 120 <= words <= 650
            else 0
        )
        +
        (
            5 if avg_sentence <= 24
            else 3 if avg_sentence <= 30
            else 0
        )
    )

    if not re.search(
        r"\b("
        r"stuff|whatever|probably|kinda|sort of"
        r")\b",
        text,
        re.I
    ):
        clarity += 4

    scores["Writing Clarity"] = min(
        clarity,
        15
    )

    scores["Personalization"] = min(
        (5 if company else 0)
        +
        (
            3 if re.search(
                r"\b("
                r"because|particularly|specifically"
                r")\b",
                text,
                re.I
            )
            else 0
        )
        +
        (
            2
            if "your company"
            not in text.lower()
            else 0
        ),
        10
    )

    scores["Completeness"] = min(
        (4 if words >= 150 else 0)
        + (2 if greeting else 0)
        + (2 if closing else 0)
        + (2 if interest else 0),
        10
    )

    total = max(
        1,
        min(
            sum(scores.values()),
            100
        )
    )

    if total >= 85:
        rating = "Excellent"

    elif total >= 70:
        rating = "Strong"

    elif total >= 55:
        rating = "Average"

    elif total >= 40:
        rating = "Needs Improvement"

    else:
        rating = "Weak"

    strengths = []
    improvements = []

    checks = [

        (
            scores["Contact Information"] >= 8,
            "Includes clear applicant contact information.",
            "Add your full name, email, phone number, and LinkedIn profile."
        ),

        (
            scores["Professional Structure"] >= 12,
            "Uses a clear professional cover letter structure.",
            "Include a professional greeting, body paragraphs, and closing."
        ),

        (
            scores["Job Relevance"] >= 15,
            "Connects the applicant's background to the target role.",
            "Explain why you want this role and connect experience to requirements."
        ),

        (
            scores["Skills and Qualifications"] >= 14,
            "Provides strong evidence of relevant skills and qualifications.",
            "Add more relevant skills, accomplishments, and measurable results."
        ),

        (
            scores["Writing Clarity"] >= 12,
            "Writing is concise, professional, and easy to read.",
            "Use clearer wording, shorter sentences, and a professional tone."
        ),

        (
            scores["Personalization"] >= 7,
            "The letter appears tailored to the employer.",
            "Mention the employer by name and explain why it interests you."
        ),

        (
            scores["Completeness"] >= 8,
            "Includes the major expected cover letter components.",
            "Add a clear introduction, qualifications, employer connection, and closing."
        )
    ]

    for passed, good, fix in checks:

        if passed:
            strengths.append(good)

        else:
            improvements.append(fix)

    return {
        **details,

        "word_count": words,

        "summary": summarize(text),

        "score": total,

        "rating": rating,

        "category_scores": scores,

        "strengths": strengths,

        "improvements": improvements,

        "readability": {
            "sentence_count": sentences,
            "average_sentence_length": round(
                avg_sentence,
                1
            )
        },

        "job_match": match
    }


# --------------------------------------------------
# RESUME PARSER
# --------------------------------------------------

def parse_resume(
    text,
    job_description=""
):

    details = extract_common_details(text)

    skills = details["skills"]
    actions = details["action_verbs"]
    metrics = details["metrics"]

    words = count_words(text)

    match = job_match(
        text,
        job_description
    )

    sections = {

        "Summary": bool(
            re.search(
                r"(?mi)^\s*"
                r"(professional summary|summary|profile|objective)"
                r"\s*:?\s*$",
                text
            )
        ),

        "Experience": bool(
            re.search(
                r"(?mi)^\s*"
                r"(work experience|professional experience|experience|employment)"
                r"\s*:?\s*$",
                text
            )
        ),

        "Education": bool(
            re.search(
                r"(?mi)^\s*education\s*:?\s*$",
                text
            )
        ),

        "Skills": bool(
            re.search(
                r"(?mi)^\s*"
                r"(skills|technical skills|core competencies)"
                r"\s*:?\s*$",
                text
            )
        ),

        "Projects": bool(
            re.search(
                r"(?mi)^\s*"
                r"(projects|academic projects|personal projects)"
                r"\s*:?\s*$",
                text
            )
        ),

        "Certifications": bool(
            re.search(
                r"(?mi)^\s*"
                r"(certifications|licenses|certificates)"
                r"\s*:?\s*$",
                text
            )
        )
    }

    education_terms = bool(
        re.search(
            r"\b("
            r"B\.?A\.?"
            r"|B\.?S\.?"
            r"|M\.?A\.?"
            r"|M\.?S\.?"
            r"|Ph\.?D\.?"
            r"|bachelor'?s?"
            r"|master'?s?"
            r"|associate'?s?"
            r"|university"
            r"|college"
            r")\b",
            text,
            re.I
        )
    )

    bullet_count = len(
        re.findall(
            r"(?m)^\s*(?:[-•*]|\d+[.)])\s+",
            text
        )
    )

    scores = {}


    # CONTACT INFORMATION - 10
    scores["Contact Information"] = min(

        (3 if details["name"] else 0)

        + (3 if details["email"] else 0)

        + (2 if details["phone"] else 0)

        + (2 if details["linkedin"] else 0),

        10
    )


    # STRUCTURE - 20
    structure_score = 0

    structure_score += (
        5 if sections["Experience"] else 0
    )

    structure_score += (
        5 if sections["Education"] else 0
    )

    structure_score += (
        5 if sections["Skills"] else 0
    )

    structure_score += (
        3
        if (
            sections["Summary"]
            or sections["Projects"]
        )
        else 0
    )

    structure_score += (
        2 if bullet_count >= 3 else 0
    )

    scores["Resume Structure"] = min(
        structure_score,
        20
    )


    # SKILLS / JOB RELEVANCE - 25
    relevance_score = min(
        len(skills) * 2,
        12
    )

    if match["match_percentage"] is not None:

        if match["match_percentage"] >= 45:
            relevance_score += 13

        elif match["match_percentage"] >= 30:
            relevance_score += 10

        elif match["match_percentage"] >= 15:
            relevance_score += 7

        elif match["match_percentage"] > 0:
            relevance_score += 3

    else:

        relevance_score += min(
            len(skills),
            8
        )

    scores["Skills and Job Relevance"] = min(
        relevance_score,
        25
    )


    # EXPERIENCE IMPACT - 20
    impact_score = (

        (
            8 if len(actions) >= 8

            else 6 if len(actions) >= 5

            else 4 if len(actions) >= 3

            else 2 if len(actions) >= 1

            else 0
        )

        +

        (
            8 if len(metrics) >= 4

            else 6 if len(metrics) >= 2

            else 3 if len(metrics) == 1

            else 0
        )

        +

        (
            4 if bullet_count >= 5

            else 2 if bullet_count >= 2

            else 0
        )
    )

    scores["Experience Impact"] = min(
        impact_score,
        20
    )


    # EDUCATION - 10
    education_score = 0

    education_score += (
        6 if sections["Education"] else 0
    )

    education_score += (
        4 if education_terms else 0
    )

    scores["Education"] = min(
        education_score,
        10
    )


    # ATS READABILITY - 15
    ats_score = 0

    ats_score += (
        5 if 150 <= words <= 1200

        else 3 if 100 <= words <= 1600

        else 0
    )

    section_count = len([
        value
        for value in sections.values()
        if value
    ])

    ats_score += (
        4 if section_count >= 3
        else 2
    )

    ats_score += (
        3 if bullet_count >= 3
        else 1
    )

    # Give basic credit for dates/years being present.
    has_dates = bool(
        re.search(
            r"\b(?:19|20)\d{2}\b",
            text
        )
    )

    ats_score += (
        3 if has_dates
        else 1
    )

    scores["ATS Readability"] = min(
        ats_score,
        15
    )


    total = max(
        1,
        min(
            sum(scores.values()),
            100
        )
    )


    if total >= 85:
        rating = "Excellent"

    elif total >= 70:
        rating = "Strong"

    elif total >= 55:
        rating = "Average"

    elif total >= 40:
        rating = "Needs Improvement"

    else:
        rating = "Weak"


    strengths = []
    improvements = []


    checks = [

        (
            scores["Contact Information"] >= 8,

            "Includes clear applicant contact information.",

            "Add your name, email, phone number, and LinkedIn profile."
        ),

        (
            scores["Resume Structure"] >= 15,

            "Uses recognizable resume sections and organization.",

            "Use clear sections such as Experience, Education, and Skills."
        ),

        (
            scores["Skills and Job Relevance"] >= 18,

            "Shows a strong set of relevant skills and keywords.",

            "Add skills and terminology that are genuinely relevant to the target job."
        ),

        (
            scores["Experience Impact"] >= 14,

            "Uses action-oriented accomplishments and measurable results.",

            "Strengthen experience bullets with action verbs and measurable outcomes."
        ),

        (
            scores["Education"] >= 8,

            "Education information is clearly represented.",

            "Add a clearly labeled Education section with degree and school information."
        ),

        (
            scores["ATS Readability"] >= 11,

            "The resume has a structure that should be relatively easy to parse.",

            "Use standard section headings, concise bullets, and clear dates."
        )
    ]


    for passed, good, fix in checks:

        if passed:
            strengths.append(good)

        else:
            improvements.append(fix)


    return {

        **details,

        "word_count": words,

        "summary": summarize(text),

        "score": total,

        "rating": rating,

        "category_scores": scores,

        "strengths": strengths,

        "improvements": improvements,

        "sections_found": sections,

        "bullet_count": bullet_count,

        "job_match": match
    }