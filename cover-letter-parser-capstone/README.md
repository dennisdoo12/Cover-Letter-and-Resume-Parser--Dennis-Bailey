# ResumeRank - Cover Letter and Resume Parser

This Flask project can parse:

- Cover letters
- Resumes
- PDF, DOCX, and TXT files

It can extract contact information, detect common skills, score document quality,
and compare a resume or cover letter against a pasted job description.

## Run

```bash
pip install -r requirements.txt
python app.py
```

Open:

- Cover Letter Parser: http://127.0.0.1:5000
- Resume Parser: http://127.0.0.1:5000/resume

## Templates

Place these files in your `templates` folder:

- `index.html` - existing cover letter page
- `resume.html` - resume page
- `parsed_text.html` - existing parsed text page
