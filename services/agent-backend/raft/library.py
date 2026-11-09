"""Build and open the Raft shelf: PDFs in, one SQLite FTS5 file out."""
import hashlib
import json
import os
import re
import sqlite3
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SHELF_JSON = os.path.join(HERE, "shelf.json")
PDF_DIR = os.path.join(HERE, "pdf")
DB_PATH = os.environ.get("RAFT_DB", os.path.join(HERE, "raft.sqlite"))

# From Lifeboat app/library.py: words that carry no search value.
STOP = set("a an and are as at be by can do does for from how i if in is it my of on or should "
           "that the this to was we what when where which who why will with you your me about "
           "there their them they then than these those into out up down over under not no yes".split())

# From Lifeboat app/retrieve.py: everyday words mapped to the words the manuals use.
EXPAND = [
    (r"\bsmoke\b", "wildfire smoke air quality mask respirator"),
    (r"\bepi-?pens?\b", "epinephrine auto-injector anaphylaxis"),
    (r"\bheart attack\b", "myocardial infarction chest pain"),
    (r"\bheat ?stroke\b", "hyperthermia heat illness"),
    (r"\bnose ?bleeds?\b", "epistaxis"),
    (r"\bpoison (oak|ivy|sumac)\b", "urushiol rash plants"),
    (r"\b(boil|boiled) water (notice|advisory)\b", "drinking water disinfection boil"),
    (r"\bpower (outage|cut|is out)\b", "blackout generator refrigerator food safety"),
    (r"\bgenerators?\b", "generator carbon monoxide outdoors"),
    (r"\bfever\b", "temperature illness"),
]


def terms(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def chunk(text, size=1400, overlap=150):
    """Split one page of text into overlapping pieces that break at spaces."""
    text = re.sub(r"\s+", " ", text).strip()
    out, i = [], 0
    while i < len(text):
        end = min(len(text), i + size)
        if end < len(text):
            cut = text.rfind(" ", i + size // 2, end)
            end = cut if cut > 0 else end
        piece = text[i:end].strip()
        if len(piece) > 40:
            out.append(piece)
        if end >= len(text):
            break
        i = max(end - overlap, i + 1)
    return out


def create(db_path):
    db = sqlite3.connect(db_path)
    db.executescript(
        "DROP TABLE IF EXISTS passages;"
        "CREATE VIRTUAL TABLE passages USING fts5(doc UNINDEXED, title UNINDEXED, page UNINDEXED, body, tokenize='porter unicode61');"
    )
    return db


def add_passages(db, doc, title, pages):
    """pages: iterable of (page_number, text)."""
    n = 0
    for page, text in pages:
        for piece in chunk(text):
            db.execute("INSERT INTO passages(doc, title, page, body) VALUES (?,?,?,?)", (doc, title, page, piece))
            n += 1
    return n


def open_db(db_path=None):
    path = db_path or DB_PATH
    if not os.path.exists(path):
        return None
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
    return db


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-kiosk-raft-build/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def pdf_pages(path):
    from pypdf import PdfReader  # only the build step needs pypdf
    for number, page in enumerate(PdfReader(path).pages, 1):
        try:
            yield number, page.extract_text() or ""
        except Exception:
            yield number, ""


def build(only=None):
    """Download each shelf PDF, index it, write raft.sqlite. Returns a report (list of dicts)."""
    os.makedirs(PDF_DIR, exist_ok=True)
    items = json.load(open(SHELF_JSON))["items"]
    tmp = DB_PATH + ".new"
    if os.path.exists(tmp):
        os.remove(tmp)
    db = create(tmp)
    report = []
    for it in items:
        if only and it["id"] not in only:
            continue
        path = os.path.join(PDF_DIR, it["id"] + ".pdf")
        row = {"id": it["id"], "license": it["license"], "url": it["url"]}
        try:
            if not os.path.exists(path):
                download(it["url"], path)
            pages = list(pdf_pages(path))
            row.update(sha256=sha256(path), pages=len(pages), passages=add_passages(db, it["id"], it["title"], pages))
        except Exception as e:
            row["error"] = type(e).__name__ + ": " + str(e)[:80]
        report.append(row)
    db.commit()
    db.close()
    os.replace(tmp, DB_PATH)
    return report
