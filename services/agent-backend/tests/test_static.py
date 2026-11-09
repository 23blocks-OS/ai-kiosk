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


def test_health_needs_no_key_but_the_kiosk_api_does():
    assert client.get("/health").status_code == 200
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 401  # spec 22


def test_kiosk_has_home_button_and_idle_reset():
    page = client.get("/apps/kiosk-intercambio/").text
    assert 'id="home"' in page and 'href="../launcher/"' in page
    js = client.get("/apps/kiosk-intercambio/app.js").text
    assert "IDLE_SECONDS" in js and "../launcher/" in js


def test_app_only_host_has_no_v1(tmp_path, monkeypatch):
    _keys(tmp_path, monkeypatch, {"alice": "k-alice"})
    monkeypatch.setattr(main, "APP_ONLY_HOSTS", {"kiosk.ciaocorp.com"})
    monkeypatch.setattr(main, "OLLAMA_HOST", "http://127.0.0.1:9")
    auth = {"Authorization": "Bearer k-alice"}
    # app-only host: 404 even with a valid key; the app itself still works
    assert client.get("/v1/models", headers={**auth, "Host": "kiosk.ciaocorp.com"}).status_code == 404
    assert client.get("/apps/kiosk-intercambio/", headers={"Host": "kiosk.ciaocorp.com"}).status_code == 200
    # other hosts (team hostname, tailnet) still reach /v1: past auth, Ollama down -> 502
    assert client.get("/v1/models", headers={**auth, "Host": "aureliano.twofourai.com"}).status_code == 502
    assert client.get("/v1/models", headers={**auth, "Host": "100.104.207.74:8000"}).status_code == 502


def test_v1_checks_key_before_anything_reaches_ollama(tmp_path, monkeypatch):
    _keys(tmp_path, monkeypatch, {"alice": "k-alice"})
    opened = []

    class Boom:  # any HTTP client opened (that is, any call toward Ollama) is recorded
        def __init__(self, *a, **k):
            opened.append(1)

    monkeypatch.setattr(main.httpx, "AsyncClient", Boom)
    for headers in ({}, {"Authorization": "Bearer wrong"}, {"X-API-Key": ""}):
        assert client.get("/v1/models", headers=headers).status_code == 401
        assert client.post("/v1/chat/completions", json={"messages": []}, headers=headers).status_code == 401
        # even a broken body gets 401, not 400: the key is checked first
        assert client.post("/v1/chat/completions", content=b"not json", headers=headers).status_code == 401
    assert opened == []


def test_pages_are_never_served_stale_after_a_deploy():
    # "no-store", not "no-cache": Cloudflare overrides no-cache with max-age=14400 for .js/.css
    for path in ("/apps/kiosk-intercambio/", "/apps/kiosk-intercambio/app.js", "/apps/launcher/styles.css", "/packages/shared-ui/agent.css"):
        assert client.get(path).headers["cache-control"] == "no-store", path


def test_the_false_demo_text_is_gone():
    js = client.get("/apps/kiosk-intercambio/app.js").text
    assert "not connected to the local model" not in js and "no estoy conectado" not in js
    assert "couldn't reach the agent" in js


def test_favicon_is_served_without_a_key():
    r = client.get("/favicon.ico")
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in r.content


def test_shop_kiosk_page_samples_and_config():
    page = client.get("/apps/kiosk-shop/").text
    assert 'data-sample="sales"' in page and 'href="../launcher/"' in page
    js = client.get("/apps/kiosk-shop/app.js").text
    assert js.count('kiosk: "shop"') == 2
    for name in ("sales", "inventory", "settings"):
        r = client.get(f"/apps/kiosk-shop/samples/{name}.png")
        assert r.status_code == 200 and r.content[:4] == b"\x89PNG"
    assert 'href="../kiosk-shop/"' in client.get("/apps/launcher/").text


def test_shop_page_gets_only_its_own_key(tmp_path, monkeypatch):
    f = tmp_path / "k.json"
    f.write_text('{"app:shop": "k-shop", "app:intercambio": "k-int"}')
    monkeypatch.setattr(main, "API_KEYS_FILE", str(f))
    cfg = client.get("/apps/kiosk-shop/config.js").text
    assert "k-shop" in cfg and "k-int" not in cfg
