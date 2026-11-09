"""Spec 22: every route that reaches the model needs a key; apps are service users."""
import json
import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main  # noqa: E402

client = TestClient(main.app)
USERS = {"alice": "k-alice", "app:intercambio": "k-app"}
PERSON = {"Authorization": "Bearer k-alice"}
APP = {"Authorization": "Bearer k-app"}


def _setup(tmp_path, monkeypatch, keys=USERS):
    f = tmp_path / "api-keys.json"
    f.write_text(json.dumps(keys))
    monkeypatch.setattr(main, "API_KEYS_FILE", str(f))

    async def fake_model(message, lang, image_base64, kiosk="intercambio"):
        return "ok"  # never call the real model from a test

    monkeypatch.setattr(main, "_call_ollama", fake_model)


def test_kiosk_routes_need_a_key_and_never_reach_ollama_without_one(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    opened = []

    class Boom:  # any HTTP client opened is a call toward Ollama
        def __init__(self, *a, **k):
            opened.append(1)

    monkeypatch.setattr(main.httpx, "AsyncClient", Boom)
    for headers in ({}, {"Authorization": "Bearer wrong"}):
        assert client.post("/api/chat", json={"message": "hi"}, headers=headers).status_code == 401
        assert client.post("/api/vision", json={"image_base64": "AAAA"}, headers=headers).status_code == 401
        # a broken body still gets 401: the key is checked before the body is read
        assert client.post("/api/chat", content=b"not json", headers=headers).status_code == 401
    assert opened == []


def test_person_key_and_app_key_work_on_kiosk_routes(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    for headers in (PERSON, APP):
        r = client.post("/api/chat", json={"message": "hi"}, headers=headers)
        assert r.status_code == 200 and r.json()["reply"] == "ok"
        r = client.post("/api/vision", json={"message": "x", "image_base64": "AAAA"}, headers=headers)
        assert r.status_code == 200


def test_app_key_is_refused_on_v1(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert client.get("/v1/models", headers=APP).status_code == 403
    assert client.post("/v1/chat/completions", json={"messages": []}, headers=APP).status_code == 403
    monkeypatch.setattr(main, "OLLAMA_HOST", "http://127.0.0.1:9")  # nothing there
    assert client.get("/v1/models", headers=PERSON).status_code == 502  # past auth, Ollama down


def test_config_js_gives_the_app_its_key(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    r = client.get("/apps/kiosk-intercambio/config.js")
    assert r.status_code == 200
    assert "no-store" in r.headers["cache-control"]
    assert "k-app" in r.text and "KIOSK_CONFIG" in r.text
    assert "k-alice" not in r.text  # a person's key never goes into a page
    # the key is never in the static page or the script
    assert "k-app" not in client.get("/apps/kiosk-intercambio/").text
    assert "k-app" not in client.get("/apps/kiosk-intercambio/app.js").text


def test_config_js_is_404_without_an_app_key(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, keys={"alice": "k-alice"})
    assert client.get("/apps/kiosk-intercambio/config.js").status_code == 404
    assert client.get("/apps/alice/config.js").status_code == 404  # cannot be used to read a person's key
    monkeypatch.setattr(main, "API_KEYS_FILE", str(tmp_path / "missing.json"))
    assert client.get("/apps/kiosk-intercambio/config.js").status_code == 404


def test_health_and_page_assets_stay_open(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert client.get("/health").status_code == 200
    assert client.get("/apps/kiosk-intercambio/").status_code == 200
    assert client.get("/apps/kiosk-intercambio/app.js").status_code == 200


def test_page_loads_config_and_sends_the_key():
    page = client.get("/apps/kiosk-intercambio/").text
    assert '<script src="config.js"></script>' in page
    assert page.index("config.js") < page.index("app.js")
    js = client.get("/apps/kiosk-intercambio/app.js").text
    assert "KIOSK_CONFIG" in js and "Authorization" in js and "not_authorized" in js
