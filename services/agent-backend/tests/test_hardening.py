"""Hardening spec: size limits, warm model, honest timeouts, one log line per call."""
import asyncio
import json
import os
import sys
import time

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main  # noqa: E402

client = TestClient(main.app)
PERSON = {"Authorization": "Bearer k-alice"}
APP = {"Authorization": "Bearer k-app"}
BIG = b"x" * 9_000_000  # over the 8 MB default


class FakeResp:
    status_code = 200

    def __init__(self, data):
        self._data = data
        self.content = json.dumps(data).encode()

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def fake_ollama(monkeypatch, behavior=None):
    """Replace the HTTP client toward Ollama. behavior: an exception to raise, or a dict to return."""
    calls = []

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, **k):
            calls.append((url, json))
            if isinstance(behavior, Exception):
                raise behavior
            return FakeResp(behavior or {"message": {"content": "hola"}})

        get = post

    monkeypatch.setattr(main.httpx, "AsyncClient", FakeClient)
    return calls


def keys(tmp_path, monkeypatch):
    f = tmp_path / "api-keys.json"
    f.write_text(json.dumps({"alice": "k-alice", "app:intercambio": "k-app"}))
    monkeypatch.setattr(main, "API_KEYS_FILE", str(f))


def test_oversized_bodies_are_refused_before_anything_reaches_ollama(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch)
    for path in ("/api/chat", "/api/vision", "/v1/chat/completions"):
        r = client.post(path, content=BIG, headers={**PERSON, "Content-Type": "application/json"})
        assert r.status_code == 413, path
    assert calls == []


def test_a_body_with_no_length_is_refused(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch)
    r = client.post("/api/chat", content=(b"x" for _ in range(3)), headers=PERSON)  # chunked: no Content-Length
    assert r.status_code == 411 and calls == []


def test_a_very_long_question_is_refused(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    fake_ollama(monkeypatch)
    assert client.post("/api/chat", json={"message": "y" * 4001}, headers=APP).status_code == 413
    assert client.post("/api/chat", json={"message": "y" * 4000}, headers=APP).status_code == 200


def test_a_timeout_is_not_called_a_missing_model(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    fake_ollama(monkeypatch, httpx.ReadTimeout("slow"))
    r = client.post("/api/chat", json={"message": "hi", "lang": "en"}, headers=APP)
    d = r.json()
    assert r.status_code == 504 and d["timeout"] is True and d["stub"] is False
    assert "longer than usual" in d["reply"] and "not connected" not in d["reply"].lower()
    es = client.post("/api/chat", json={"message": "hola", "lang": "es"}, headers=APP).json()
    assert "más de lo normal" in es["reply"]


def test_unreachable_ollama_still_gets_the_honest_stub(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    fake_ollama(monkeypatch, httpx.ConnectError("down"))
    r = client.post("/api/chat", json={"message": "hi", "lang": "en"}, headers=APP)
    d = r.json()
    assert r.status_code == 200 and d["stub"] is True and d["ollama_available"] is False
    assert d["reply"].startswith("STUB")


def test_a_full_queue_gets_503(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    fake_ollama(monkeypatch)
    monkeypatch.setattr(main, "_model_sem", asyncio.Semaphore(0))
    monkeypatch.setattr(main, "MAX_QUEUE_WAIT", 0.05)
    r = client.post("/api/chat", json={"message": "hi", "lang": "en"}, headers=APP)
    assert r.status_code == 503 and "next in line" in r.json()["reply"]


def test_every_kiosk_call_keeps_the_model_loaded(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch)
    assert client.post("/api/chat", json={"message": "hi"}, headers=APP).status_code == 200
    url, payload = calls[0]
    assert url.endswith("/api/chat") and payload["keep_alive"] == -1


def test_startup_warms_the_model(monkeypatch):
    calls = fake_ollama(monkeypatch)
    with TestClient(main.app):
        for _ in range(40):  # the warm-up runs in the background
            if calls:
                break
            time.sleep(0.05)
    url, payload = calls[0]
    assert url.endswith("/api/generate")
    assert payload["model"] == main.OLLAMA_MODEL and payload["keep_alive"] == -1 and "prompt" not in payload


def test_one_log_line_per_call_with_no_question_text(tmp_path, monkeypatch, capsys):
    keys(tmp_path, monkeypatch)
    secret = "mi-pregunta-privada-xyz"
    fake_ollama(monkeypatch)
    client.post("/api/chat", json={"message": secret}, headers=APP)
    fake_ollama(monkeypatch, httpx.ReadTimeout("slow"))
    client.post("/api/chat", json={"message": secret}, headers=APP)
    fake_ollama(monkeypatch, httpx.ConnectError("down"))
    client.post("/api/chat", json={"message": secret}, headers=APP)
    out = capsys.readouterr().out
    lines = [ln for ln in out.splitlines() if ln.startswith("call ")]
    assert len(lines) == 3
    assert "route=chat user=app:intercambio outcome=ok ms=" in lines[0] and "model=" in lines[0]
    assert "outcome=timeout" in lines[1] and "outcome=unreachable" in lines[2]
    assert secret not in out and "k-app" not in out  # no question text, no key value
    assert "model_error reason=ReadTimeout" in out


def test_refused_calls_are_logged_without_the_key(tmp_path, monkeypatch, capsys):
    keys(tmp_path, monkeypatch)
    client.post("/api/chat", json={"message": "hi"})
    client.post("/api/chat", json={"message": "hi"}, headers={"Authorization": "Bearer secret-wrong-key"})
    client.get("/v1/models", headers=APP)
    out = capsys.readouterr().out
    assert "refused path=/api/chat why=missing" in out
    assert "refused path=/api/chat why=bad_key" in out
    assert "refused path=/v1/models why=app_key_on_v1" in out
    assert "secret-wrong-key" not in out and "k-app" not in out


def test_v1_body_that_is_not_an_object_gets_400(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    fake_ollama(monkeypatch)
    r = client.post("/v1/chat/completions", json=["not", "an", "object"], headers=PERSON)
    assert r.status_code == 400


def test_prompt_follows_visitor_language_not_a_spanish_default(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch)
    client.post("/api/chat", json={"message": "How do I book?", "lang": "en"}, headers=APP)
    system = calls[-1][1]["messages"][0]["content"]
    assert "Spanish is the default" not in system
    assert "language of the visitor's last message" in system
    assert system.endswith("answer in English.")


def test_vision_upload_sends_the_image_to_the_model(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch, {"message": {"content": "a letter"}})
    r = client.post("/api/vision", files={"image": ("a.png", b"\x89PNG-bytes", "image/png")}, data={"lang": "en"}, headers=APP)
    assert r.status_code == 200 and r.json()["reply"] == "a letter"
    assert r.json()["bytes_received"] == len(b"\x89PNG-bytes")
    assert calls[-1][1]["messages"][1]["images"]


def test_vision_without_an_image_is_400_and_never_reaches_the_model(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch)
    r = client.post("/api/vision", json={"message": "read this"}, headers=APP)
    assert r.status_code == 400 and r.json()["stub"] is True
    assert calls == []


def test_unknown_kiosk_is_400_and_never_reaches_the_model(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch)
    r = client.post("/api/chat", json={"message": "hi", "kiosk": "nope"}, headers=PERSON)
    assert r.status_code == 400 and calls == []


def test_each_kiosk_gets_its_own_prompt(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch)
    client.post("/api/chat", json={"message": "hi", "kiosk": "shop"}, headers=PERSON)
    client.post("/api/chat", json={"message": "hi", "kiosk": "intercambio"}, headers=PERSON)
    shop, interc = (c[1]["messages"][0]["content"] for c in calls[-2:])
    assert "Shop Operator" in shop and "Intercambio" in interc and shop != interc


def test_default_kiosk_is_intercambio(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch)
    client.post("/api/chat", json={"message": "hi"}, headers=APP)
    assert "Intercambio" in calls[-1][1]["messages"][0]["content"]


def test_an_app_key_cannot_use_another_kiosk(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch)
    r = client.post("/api/chat", json={"message": "hi", "kiosk": "shop"}, headers=APP)  # app:intercambio
    assert r.status_code == 403 and calls == []


def test_vision_takes_the_kiosk_too(tmp_path, monkeypatch):
    keys(tmp_path, monkeypatch)
    calls = fake_ollama(monkeypatch, {"message": {"content": "click Print"}})
    r = client.post("/api/vision", json={"image_base64": "aGk=", "kiosk": "shop"}, headers=PERSON)
    assert r.status_code == 200 and "Shop Operator" in calls[-1][1]["messages"][0]["content"]
