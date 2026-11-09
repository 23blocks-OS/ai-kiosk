"""Find the best three passages for a question (BM25), or none."""
import re

from .library import EXPAND, terms

MAX_PASSAGES = 3
MAX_CHARS = 1200
PER_DOC = 2


def expand(question):
    extra = [words for pat, words in EXPAND if re.search(pat, question, re.I)]
    return " ".join([question, *extra])


def search(db, question, n=MAX_PASSAGES):
    """Return up to n passages: [{doc, title, page, text}]. Empty when the shelf does not cover it."""
    wanted = set(terms(question))
    if not wanted or db is None:
        return []
    fts = " OR ".join(f'"{w}"' for w in sorted(set(terms(expand(question))))[:24])
    rows = db.execute(
        "SELECT doc, title, page, body FROM passages WHERE passages MATCH ? ORDER BY bm25(passages) LIMIT 30", (fts,)
    ).fetchall()
    need = 1 if len(wanted) == 1 else 2  # a passage must hold at least two of the question's own words
    out, per_doc = [], {}
    for doc, title, page, body in rows:
        have = len(wanted & set(terms(body)))
        if have < need or per_doc.get(doc, 0) >= PER_DOC:
            continue
        per_doc[doc] = per_doc.get(doc, 0) + 1
        out.append({"doc": doc, "title": title, "page": page, "text": body[:MAX_CHARS]})
        if len(out) >= n:
            break
    return out
