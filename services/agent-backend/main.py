"""Agent backend — FastAPI service on the Jetson, wired to Ollama.

Flow: kiosk web UI -> this backend -> Ollama (localhost:11434,
Qwen3-VL 4B) -> reply. No cloud service is called, ever.

Honest fallback: if Ollama is unreachable, errors, or times out, the
endpoints return the canned demo reply with ``stub: true`` and
``ollama_available: false``. They never fake a model answer.

Concurrency: at most MAX_CONCURRENT_MODEL_CALLS (default 2) model
calls run at once — the 8 GB Jetson shares one GPU, so 1 user gets
full speed, 2 get about half each, and a 3rd waits in line (503 after
MAX_QUEUE_WAIT_SECONDS).
"""

import asyncio
import base64
import hmac
import json
import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-vl:4b")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "120"))
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT_MODEL_CALLS", "2"))
MAX_QUEUE_WAIT = float(os.environ.get("MAX_QUEUE_WAIT_SECONDS", "30"))
# Who may call /v1/*: a JSON file {"name": "key"}, never committed (see api-keys.example.json).
API_KEYS_FILE = os.environ.get(
    "API_KEYS_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "api-keys.json")
)

SYSTEM_PROMPT = (
    "You are the Intercambio kiosk helper in Boulder, Colorado. "
    "You help Spanish-speaking newcomers read, explain, and translate "
    "forms, letters, and notices, and navigate local services and "
    "appointments (where, when, what to bring, how to book). "
    "Answer in the language the visitor used; Spanish is the default. "
    "Use short, clear, plain language. "
    "This is navigation, NOT legal advice: if a question is about "
    "immigration status, rights, or legal strategy, say so plainly "
    "and point the person to a human helper. Never invent facts from "
    "a document you cannot read."
)

app = FastAPI(title="ai-kiosk agent-backend")

# Concurrency guard: one semaphore for all model calls.
_model_sem = asyncio.Semaphore(MAX_CONCURRENT)
_waiting = 0


class ChatRequest(BaseModel):
    message: str
    lang: str = "es"
    image_base64: str | None = None


class VisionRequest(BaseModel):
    message: str = "Lee este documento y explícalo en español."
    lang: str = "es"
    image_base64: str


def _stub_reply(lang: str) -> str:
    if (lang or "es").startswith("en"):
        return (
            "STUB — no local model connected yet. When the Jetson is ready, "
            "this reply will come from Qwen3-VL 4B running on-device."
        )
    return (
        "STUB — todavía no hay modelo local conectado. Cuando el Jetson "
        "esté listo, esta respuesta vendrá de Qwen3-VL 4B corriendo en el equipo."
    )


def _queue_reply(lang: str) -> str:
    if (lang or "es").startswith("en"):
        return (
            "2 people are using the agent right now, you're next in line. "
            "Please wait a moment and try again."
        )
    return (
        "Hay 2 personas usando el agente ahora mismo, eres el siguiente "
        "en la fila. Espera un momento e inténtalo de nuevo."
    )


async def _ollama_available() -> bool:
    try:
        # trust_env=False: Ollama is local-only; never route it through
        # any proxy (and httpx's proxy handling can mis-parse NO_PROXY).
        async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


async def _call_ollama(message: str, lang: str, image_base64: str | None) -> str | None:
    """Return the model's reply, or None if Ollama failed (caller falls back)."""
    user_msg: dict = {"role": "user", "content": message}
    if image_base64:
        user_msg["images"] = [image_base64]
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            user_msg,
        ],
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT, trust_env=False) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = (data.get("message") or {}).get("content", "")
            return content.strip() or None
    except Exception:
        return None


async def _guarded_model_call(message: str, lang: str, image_base64: str | None):
    """Run a model call under the concurrency guard.

    Returns (status, reply, queue_position): status is "ok", "queued"
    (503 — waited too long), or "fallback" (Ollama failed).
    """
    global _waiting
    _waiting += 1
    try:
        try:
            await asyncio.wait_for(_model_sem.acquire(), timeout=MAX_QUEUE_WAIT)
        except asyncio.TimeoutError:
            return "queued", _queue_reply(lang), _waiting
    finally:
        _waiting -= 1
    try:
        reply = await _call_ollama(message, lang, image_base64)
    finally:
        _model_sem.release()
    if reply is None:
        return "fallback", _stub_reply(lang), None
    return "ok", reply, None


def _response(status: str, reply: str, lang: str, queue_position=None, extra=None):
    body = {
        "reply": reply,
        "stub": status != "ok",
        "ollama_available": status == "ok",
        "model": OLLAMA_MODEL if status == "ok" else "not-connected",
    }
    if status == "queued":
        body["queue_position"] = queue_position
    if extra:
        body.update(extra)
    code = 503 if status == "queued" else 200
    return JSONResponse(status_code=code, content=body)


@app.get("/health")
async def health():
    available = await _ollama_available()
    return {
        "status": "ok",
        "stub": not available,
        "model": OLLAMA_MODEL if available else "not-connected",
        "ollama_available": available,
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    status, reply, queue_pos = await _guarded_model_call(
        req.message, req.lang, req.image_base64
    )
    return _response(status, reply, req.lang, queue_pos)


@app.post("/api/vision")
async def vision(request: Request):
    """Accept a base64 image (JSON) or a file upload (multipart).

    JSON: {"message", "lang", "image_base64"}. Multipart: file field
    named "image" (or "file"), plus optional "message"/"lang" fields.
    The image is used for this one answer only and is never stored.
    """
    content_type = request.headers.get("content-type", "")
    message = "Lee este documento y explícalo en español."
    lang = "es"
    image_b64: str | None = None
    filename = None
    n_bytes = 0

    if "multipart/form-data" in content_type:
        form = await request.form()
        message = str(form.get("message") or message)
        lang = str(form.get("lang") or lang)
        upload = form.get("image") or form.get("file")
        if upload is not None and hasattr(upload, "read"):
            data = await upload.read()
            filename = getattr(upload, "filename", None)
            n_bytes = len(data)
            image_b64 = base64.b64encode(data).decode("ascii")
    else:
        try:
            body = await request.json()
        except Exception:
            body = {}
        message = str(body.get("message") or message)
        lang = str(body.get("lang") or lang)
        image_b64 = body.get("image_base64")
        if image_b64:
            try:
                n_bytes = len(base64.b64decode(image_b64, validate=False))
            except Exception:
                n_bytes = 0

    if not image_b64:
        return JSONResponse(
            status_code=400,
            content={
                "reply": _stub_reply(lang),
                "stub": True,
                "ollama_available": False,
                "error": "No image supplied: send image_base64 (JSON) or an image file (multipart).",
            },
        )

    status, reply, queue_pos = await _guarded_model_call(message, lang, image_b64)
    return _response(
        status,
        reply,
        lang,
        queue_pos,
        extra={
            "description": reply,
            "filename": filename,
            "bytes_received": n_bytes,
        },
    )


# Hostnames that get the kiosk app only: /v1/* is a 404 there, even with a key.
# Set APP_ONLY_HOSTS=kiosk.ciaocorp.com (comma-separated for more).
APP_ONLY_HOSTS = {h.strip().lower() for h in os.environ.get("APP_ONLY_HOSTS", "").split(",") if h.strip()}


@app.middleware("http")
async def _app_only_hosts(request: Request, call_next):
    host = request.headers.get("host", "").split(":")[0].lower()
    if request.url.path.startswith("/v1") and host in APP_ONLY_HOSTS:
        return JSONResponse(status_code=404, content={"error": {"message": "Not found."}})
    return await call_next(request)


# ---- Team API: OpenAI-compatible, every caller needs an API key ----------
# The kiosk page's own /api/* stays open (a public page cannot hold a secret).
# /v1/* is for people and agents, on the tunnel and on the tailnet alike.


def _api_user(request: Request) -> str | None:
    """Name of the user whose key the request carries, or None."""
    auth = request.headers.get("authorization", "")
    key = auth[7:] if auth.lower().startswith("bearer ") else request.headers.get("x-api-key", "")
    try:
        with open(API_KEYS_FILE) as f:
            keys = json.load(f)
    except (OSError, ValueError):
        return None  # no key file means no keys: the API stays closed
    found = None
    for name, k in keys.items():
        if key and hmac.compare_digest(str(k), key):
            found = name
    return found


def _unauthorized() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"error": {"message": "Missing or invalid API key. Send Authorization: Bearer <key>.", "type": "invalid_api_key"}},
    )


@app.get("/v1/models")
async def v1_models(request: Request):
    if not _api_user(request):
        return _unauthorized()
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            r = await client.get(f"{OLLAMA_HOST}/v1/models")
        return Response(content=r.content, status_code=r.status_code, media_type="application/json")
    except Exception:
        return JSONResponse(status_code=502, content={"error": {"message": "Ollama is not reachable."}})


@app.post("/v1/chat/completions")
async def v1_chat(request: Request):
    """Pass-through to Ollama's OpenAI-compatible API: text and images, any installed model."""
    user = _api_user(request)
    if not user:
        return _unauthorized()
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": {"message": "Body must be JSON."}})
    if body.get("stream"):
        return JSONResponse(status_code=400, content={"error": {"message": "stream is not supported; send stream:false."}})
    body.setdefault("model", OLLAMA_MODEL)
    try:
        await asyncio.wait_for(_model_sem.acquire(), timeout=MAX_QUEUE_WAIT)
    except asyncio.TimeoutError:
        return JSONResponse(status_code=503, content={"error": {"message": "The model is busy. Try again in a moment."}})
    try:
        print(f"v1 user={user} model={body['model']}", flush=True)
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT, trust_env=False) as client:
            r = await client.post(f"{OLLAMA_HOST}/v1/chat/completions", json=body)
        return Response(content=r.content, status_code=r.status_code, media_type="application/json")
    except Exception:
        return JSONResponse(status_code=502, content={"error": {"message": "Ollama is not reachable or timed out."}})
    finally:
        _model_sem.release()


@app.get("/", include_in_schema=False)
async def root(request: Request):
    query = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(f"/apps/launcher/{query}")


# Serve the kiosk UI from the same port when run from the repo root
# (this is how the Cloudflare Tunnel mode works: one port, one origin).
# Local dev can still use a plain static server + the backend on 8001.
# Mount ONLY what the UI needs. Never the repo root: that would publish
# /.git/, the backend source and any .env through the tunnel.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if os.path.isdir(os.path.join(_REPO_ROOT, "apps", "kiosk-intercambio")):
    app.mount("/apps", StaticFiles(directory=os.path.join(_REPO_ROOT, "apps"), html=True), name="apps")
    app.mount(
        "/packages/shared-ui",
        StaticFiles(directory=os.path.join(_REPO_ROOT, "packages", "shared-ui")),
        name="shared-ui",
    )
