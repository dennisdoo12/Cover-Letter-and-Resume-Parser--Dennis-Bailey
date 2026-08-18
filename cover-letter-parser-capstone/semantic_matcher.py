"""
semantic_matcher.py
-------------------
Semantic matching layer for the resume screener.

This sits ON TOP OF the keyword/skill-overlap base layer in matcher.py.
- The base layer (score_skills) is EXPLAINABLE: it tells you exactly which
  required skills literally appeared in the resume.
- This layer is SEMANTIC: it embeds each required skill and the candidate's
  resume text, then measures cosine similarity. It catches meaning that the
  keyword layer misses (e.g. "built neural networks in PyTorch" partially
  satisfying a "Machine Learning" requirement even without the exact phrase).

Design notes:
- Uses a pretrained sentence-transformer (all-MiniLM-L6-v2) rather than
  training from scratch
"""

from functools import lru_cache

_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model():
    #Load the sentence-transformer once and cache it.
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(_MODEL_NAME)


def _cosine(a, b):
    #Cosine similarity between two 1-D vectors, using numpy.
    import numpy as np
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
#Scoring each skill against resume
def semantic_skill_scores(resume_text, required_skills, embed_fn=None):

    if not required_skills:
        return {}

    # Split the resume into non-empty lines; each line is a candidate span
    # a skill could semantically match against.
    lines = [ln.strip() for ln in resume_text.splitlines() if ln.strip()]
    if not lines:
        return {skill: 0.0 for skill in required_skills}

    if embed_fn is None:
        model = _get_model()
        embed_fn = lambda texts: model.encode(texts)

    skill_vecs = embed_fn(list(required_skills))
    line_vecs = embed_fn(lines)

    #finds the best matches for the skill
    scores = {}
    for skill, svec in zip(required_skills, skill_vecs):
        best = max(_cosine(svec, lvec) for lvec in line_vecs)
        scores[skill] = max(0.0, best)   # cosine can be slightly negative so becomes 0
    return scores

#get as one score
def semantic_score(resume_text, required_skills, threshold=0.4, embed_fn=None):

    per_skill = semantic_skill_scores(resume_text, required_skills, embed_fn)
    if not per_skill:
        return {"semantic_score": 1.0, "per_skill": {}, "semantic_hits": []}

    mean = sum(per_skill.values()) / len(per_skill)
    hits = sorted(s for s, v in per_skill.items() if v >= threshold)
    return {
        "semantic_score": round(mean, 4),
        "per_skill": {s: round(v, 4) for s, v in per_skill.items()},
        "semantic_hits": hits,
    }


# test with a fake embedder 
if __name__ == "__main__":
    import json

    # Fake embedder: maps text -> a tiny vector based on keyword presence,
    # just to prove the scoring logic runs without downloading the model.
    def fake_embed(texts):
        vocab = ["python", "machine", "learning", "neural", "sql", "react"]
        vecs = []
        for t in texts:
            tl = t.lower()
            vecs.append([1.0 if w in tl else 0.0 for w in vocab])
        return vecs

    resume = "Built neural networks in Python\nWorked with SQL databases"
    required = ["Machine Learning", "SQL", "React"]

    result = semantic_score(resume, required, embed_fn=fake_embed)
    print(json.dumps(result, indent=2))
    print("\n(This used a fake embedder for testing. With sentence-transformers")
    print("installed, real embeddings are used automatically.)")