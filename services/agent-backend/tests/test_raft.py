"""Raft: shelf search, honest 'not covered', citations, the child-dose guard."""
import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402
from raft import guard, library, retrieve  # noqa: E402

from test_hardening import fake_ollama  # noqa: E402

client = TestClient(main.app)
RAFT = {"Authorization": "Bearer k-raft"}
PERSON = {"Authorization": "Bearer k-alice"}

PASSAGES = [
    ("ready-wildfire", "Ready.gov Wildfire", 1, "When wildfire smoke is heavy outside, stay indoors with windows and doors closed. Use a HEPA air cleaner and an N95 respirator mask if you must go out."),
    ("cdc-generator", "CDC Generator CO Safety", 1, "Never run a generator inside a home or garage. Carbon monoxide from a generator can kill in minutes. Keep it outdoors, far from windows."),
    ("cdc-water", "CDC Make Water Safe", 1, "Boil water for one minute to make it safe to drink. If you cannot boil it, disinfect with unscented household bleach."),
]


@pytest.fixture
def shelf(tmp_path, monkeypatch):
    db_path = str(tmp_path / "raft.sqlite")
    db = library.create(db_path)
    for doc, title, page, text in PASSAGES:
        library.add_passages(db, doc, title, [(page, text * 2)])
    db.commit()
    db.close()
    monkeypatch.setattr(main, "RAFT_DB_PATH", db_path)
    f = tmp_path / "keys.json"
    f.write_text(json.dumps({"alice": "k-alice", "app:raft": "k-raft"}))
    monkeypatch.setattr(main, "API_KEYS_FILE", str(f))
    return db_path


def ask(q, lang="en", headers=RAFT):
    return client.post("/api/chat", json={"message": q, "kiosk": "raft", "lang": lang}, headers=headers)


def test_expand_adds_manual_words():
    assert "myocardial infarction" in retrieve.expand("I think it is a heart attack")


def test_search_finds_the_right_document(shelf):
    db = library.open_db(shelf)
    hits = retrieve.search(db, "Wildfire smoke is heavy outside. How do I protect my family indoors?")
    assert hits and hits[0]["doc"] == "ready-wildfire"
    assert retrieve.search(db, "My generator is in the garage, is that safe?")[0]["doc"] == "cdc-generator"


def test_not_covered_skips_the_model(shelf, monkeypatch):
    calls = fake_ollama(monkeypatch)
    r = ask("How do I file my taxes?")
    assert r.status_code == 200 and "don't cover this" in r.json()["reply"] and r.json()["sources"] == []
    assert calls == []


def test_answer_has_sources_and_a_prompt_with_the_rules(shelf, monkeypatch):
    calls = fake_ollama(monkeypatch, {"message": {"content": "1. Stay indoors [1]."}})
    r = ask("Wildfire smoke is heavy outside. What do I do indoors?")
    body = r.json()
    assert r.status_code == 200 and body["sources"][0]["doc"] == "ready-wildfire" and body["sources"][0]["n"] == 1
    system = calls[-1][1]["messages"][0]["content"]
    assert "Answer ONLY from the numbered SOURCES" in system and "call 911" in system and "[1] Ready.gov Wildfire" in system
    assert len(body["sources"]) <= 3


def test_spanish_not_covered(shelf, monkeypatch):
    fake_ollama(monkeypatch)
    assert "no cubren" in ask("¿Cómo declaro impuestos?", lang="es").json()["reply"]


def test_child_dose_guard():
    assert guard.dose_warning("my 4 year old has a fever", "Give 200 mg of ibuprofen.")
    assert guard.dose_warning("I have a fever", "Take 200 mg of ibuprofen.") is None
    strong = guard.dose_warning("my son is sick", "Ibuprofen up to 1,200 mg a day.")
    assert "adult daily maximum for ibuprofen" in strong


def test_guard_runs_on_the_reply(shelf, monkeypatch):
    fake_ollama(monkeypatch, {"message": {"content": "Give 400 mg now [1]."}})
    r = ask("My 4 year old swallowed smoke from the wildfire outside")
    assert r.json()["warn"]


def test_missing_shelf_is_an_honest_503(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "RAFT_DB_PATH", str(tmp_path / "none.sqlite"))
    f = tmp_path / "keys.json"
    f.write_text(json.dumps({"app:raft": "k-raft"}))
    monkeypatch.setattr(main, "API_KEYS_FILE", str(f))
    r = ask("wildfire smoke")
    assert r.status_code == 503 and r.json()["shelf_missing"] is True


def test_raft_key_is_app_scoped(shelf):
    assert client.get("/v1/models", headers=RAFT).status_code == 403


def test_raft_key_cannot_use_another_kiosk(shelf, monkeypatch):
    fake_ollama(monkeypatch)
    r = client.post("/api/chat", json={"message": "hi", "kiosk": "shop"}, headers=RAFT)
    assert r.status_code == 403


def test_the_log_has_no_question(shelf, monkeypatch, capsys):
    fake_ollama(monkeypatch)
    ask("How do I file my secretword taxes?")
    out = capsys.readouterr().out
    assert "not_covered" in out and "secretword" not in out


def test_shelf_is_public_domain():
    items = json.load(open(os.path.join(os.path.dirname(library.__file__), "shelf.json")))["items"]
    assert len(items) >= 9
    for it in items:
        assert it["license"].startswith("US Gov public domain")
        assert it["url"].startswith("https://") and any(h in it["url"] for h in (".gov", "ciehub.info"))


@pytest.mark.skipif(not os.path.exists(library.DB_PATH), reason="real shelf not built on this machine")
def test_real_shelf_finds_the_demo_questions():
    db = library.open_db()
    cases = {
        "Wildfire smoke is heavy outside. How do I protect my family indoors?": ("epa-wildfire-smoke-guide", "ready-wildfire-info-sheet"),
        "Is it safe to run a generator in my garage?": ("cdc-generator-co-safety", "cpsc-generator-safety", "ready-power-outage-info-sheet"),
        "How do I make water safe to drink in an emergency?": ("cdc-make-water-safe",),
        "How do I treat a deep cut that is bleeding?": ("tc-4-02-1-first-aid",),
        "I touched poison ivy. What do I do?": ("niosh-poisonous-plants",),
    }
    for q, docs in cases.items():
        hits = retrieve.search(db, q)
        assert hits and hits[0]["doc"] in docs, (q, [h["doc"] for h in hits])
    assert retrieve.search(db, "How do I file my taxes?") == []


def test_sources_are_hidden_when_the_answer_cites_nothing(shelf, monkeypatch):
    fake_ollama(monkeypatch, {"message": {"content": "My sources don't cover this."}})
    body = ask("Wildfire smoke is heavy outside. What do I do indoors?").json()
    assert body["sources"] == []
