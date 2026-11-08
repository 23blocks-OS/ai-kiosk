"""The public origin must serve the kiosk UI and nothing else from disk."""
import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import app  # noqa: E402

client = TestClient(app)


def test_ui_is_served():
    assert client.get("/apps/kiosk-intercambio/").status_code == 200
    assert client.get("/apps/kiosk-intercambio/app.js").status_code == 200
    assert client.get("/packages/shared-ui/agent.css").status_code == 200


def test_health_still_works():
    assert client.get("/health").status_code == 200


def test_repo_internals_are_not_served():
    for path in (
        "/.git/config",
        "/.git/HEAD",
        "/.env",
        "/.gitignore",
        "/services/agent-backend/main.py",
        "/services/agent-backend/.env.example",
        "/hardware/jetson/cloudflared/config.yml.example",
        "/packages/shared-ui/../../.git/config",
        "/apps/../.git/config",
        "/apps/%2e%2e/.git/config",
    ):
        assert client.get(path).status_code == 404, path


def test_root_goes_to_selector_and_keeps_query():
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == "/apps/launcher/"
    r = client.get("/?mode=remote", follow_redirects=False)
    assert r.headers["location"] == "/apps/launcher/?mode=remote"


def test_selector_page_and_its_target_exist():
    page = client.get("/apps/launcher/")
    assert page.status_code == 200
    assert 'href="../kiosk-intercambio/"' in page.text
    assert client.get("/apps/launcher/app.js").status_code == 200
    assert client.get("/apps/launcher/styles.css").status_code == 200
    assert client.get("/apps/kiosk-intercambio/").status_code == 200


# ---- /v1 API keys ----------------------------------------------------------
import json  # noqa: E402

import main  # noqa: E402


def _keys(tmp_path, monkeypatch, data):
    f = tmp_path / "api-keys.json"
    f.write_text(json.dumps(data))
    monkeypatch.setattr(main, "API_KEYS_FILE", str(f))


def test_v1_closed_without_key_file(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "API_KEYS_FILE", str(tmp_path / "missing.json"))
    assert client.get("/v1/models").status_code == 401
    assert client.post("/v1/chat/completions", json={}).status_code == 401


def test_v1_rejects_missing_and_wrong_key(tmp_path, monkeypatch):
    _keys(tmp_path, monkeypatch, {"alice": "k-alice"})
    assert client.get("/v1/models").status_code == 401
    assert client.get("/v1/models", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert client.get("/v1/models", headers={"Authorization": ""}).status_code == 401


def test_v1_accepts_bearer_and_x_api_key(tmp_path, monkeypatch):
    _keys(tmp_path, monkeypatch, {"alice": "k-alice"})
    monkeypatch.setattr(main, "OLLAMA_HOST", "http://127.0.0.1:9")  # nothing there
    for h in ({"Authorization": "Bearer k-alice"}, {"X-API-Key": "k-alice"}):
        assert client.get("/v1/models", headers=h).status_code == 502  # past auth, Ollama down


def test_v1_rejects_streaming(tmp_path, monkeypatch):
    _keys(tmp_path, monkeypatch, {"alice": "k-alice"})
    r = client.post("/v1/chat/completions", json={"stream": True}, headers={"Authorization": "Bearer k-alice"})
    assert r.status_code == 400


def test_kiosk_api_and_health_need_no_key():
    assert client.get("/health").status_code == 200
    assert client.post("/api/chat", json={"message": "hi"}).status_code in (200, 503)
