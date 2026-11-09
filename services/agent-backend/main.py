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
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-vl:4b")
# Answer before Cloudflare gives up on a tunnel request (about 100 s).
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "90"))
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT_MODEL_CALLS", "2"))
MAX_QUEUE_WAIT = float(os.environ.get("MAX_QUEUE_WAIT_SECONDS", "30"))
MAX_BODY_BYTES = int(float(os.environ.get("MAX_BODY_MB", "8")) * 1_000_000)
MAX_QUESTION_CHARS = 4000
# Who may call /v1/*: a JSON file {"name": "key"}, never committed (see api-keys.example.json).
API_KEYS_FILE = os.environ.get(
    "API_KEYS_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "api-keys.json")
)

SYSTEM_PROMPT = (
    "You are the Intercambio kiosk helper in Boulder, Colorado. "
    "You help Spanish-speaking newcomers read, explain, and translate "
    "forms, letters, and notices, and navigate local services and "
    "appointments (where, when, what to bring, how to book). "
    "Answer in the language of the visitor's last message. "
    "Use short, clear, plain language. "
    "This is navigation, NOT legal advice: if a question is about "
    "immigration status, rights, or legal strategy, say so plainly "
    "and point the person to a human helper. Never invent facts from "
    "a document you cannot read."
)

SHOP_PROMPT = (
    "You are the Shop Operator helper for a small shop. The visitor shows a screenshot of "
    "the shop's Windows program and asks how to do a task. "
    "Describe only what is visible on the screen. Name the exact button, tab or menu to use, "
    "and give short numbered steps. "
    "If the button or setting is not on this screen, say \"I cannot see that on this screen\" "
    "and say what to open first. Never guess a setting or invent a menu. "
    "Answer in the language of the visitor's last message. Use short, plain language. "
    "The shop is fictional; never ask for passwords, card numbers or customer data."
)

# One prompt per kiosk. A kiosk page sends its own name in the "kiosk" field.
PROMPTS = {"intercambio": SYSTEM_PROMPT, "shop": SHOP_PROMPT}
DEFAULT_KIOSK = "intercambio"


async def _warm_model():
    """Load the model at startup so the first visitor is not the one who waits."""
    outcome = "ok"
    try:
        async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
            await client.post(f"{OLLAMA_HOST}/api/generate", json={"model": OLLAMA_MODEL, "keep_alive": -1})
    except Exception as e:
        outcome = type(e).__name__
    print(f"warmup model={OLLAMA_MODEL} outcome={outcome}", flush=True)


@asynccontextmanager
async def _lifespan(_app):
    task = asyncio.create_task(_warm_model())
    yield
    task.cancel()


app = FastAPI(title="ai-kiosk agent-backend", lifespan=_lifespan)

# Concurrency guard: one semaphore for all model calls.
_model_sem = asyncio.Semaphore(MAX_CONCURRENT)
_waiting = 0


class ChatRequest(BaseModel):
    message: str
    lang: str = "es"
    kiosk: str = DEFAULT_KIOSK
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


def _timeout_reply(lang: str) -> str:
    if (lang or "es").startswith("en"):
        return "The agent is taking longer than usual. Please try again in a moment."
    return "El agente está tardando más de lo normal. Inténtalo de nuevo en un momento."


class ModelFailure(Exception):
    """The model call failed. outcome: timeout | unreachable | error | empty."""

    def __init__(self, outcome: str):
        super().__init__(outcome)
        self.outcome = outcome


def _log_error(e: Exception):
    print(f"model_error reason={type(e).__name__}", flush=True)  # class name only, never content


def _log_call(route: str, user: str, outcome: str, t0: float, model: str | None = None):
    # One line per model call. Never the question, the answer, an image, an address or a key.
    ms = round((time.monotonic() - t0) * 1000)
    print(f"call route={route} user={user} outcome={outcome} ms={ms} model={model or OLLAMA_MODEL}", flush=True)


async def _ollama_available() -> bool:
    try:
        # trust_env=False: Ollama is local-only; never route it through
        # any proxy (and httpx's proxy handling can mis-parse NO_PROXY).
        async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


def _language_hint(lang: str) -> str:
    """Tell the model which language to use when the message does not show one."""
    name = "English" if (lang or "es").startswith("en") else "Spanish"
    return f" If you cannot tell which language the visitor wrote, answer in {name}."


async def _call_ollama(message: str, lang: str, image_base64: str | None, kiosk: str = DEFAULT_KIOSK) -> str:
    """Return the model's reply, or raise ModelFailure (the caller falls back honestly)."""
    user_msg: dict = {"role": "user", "content": message}
    if image_base64:
        user_msg["images"] = [image_base64]
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": PROMPTS[kiosk] + _language_hint(lang)},
            user_msg,
        ],
        "stream": False,
        "keep_alive": -1,  # keep the model loaded: a cold start is longer than Cloudflare waits
    }
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT, trust_env=False) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException as e:
        _log_error(e)
        raise ModelFailure("timeout")
    except httpx.ConnectError as e:
        _log_error(e)
        raise ModelFailure("unreachable")
    except Exception as e:
        _log_error(e)
        raise ModelFailure("error")
    content = ((data.get("message") or {}).get("content", "") or "").strip()
    if not content:
        raise ModelFailure("empty")
    return content


async def _guarded_model_call(message: str, lang: str, image_base64: str | None, route: str = "chat", user: str = "-", kiosk: str = DEFAULT_KIOSK):
    """Run a model call under the concurrency guard.

    Returns (status, reply, queue_position): status is "ok", "queued" (503: waited
    too long), "timeout" (504: the model took too long) or "fallback" (Ollama failed).
    """
    global _waiting
    t0 = time.monotonic()
    _waiting += 1
    try:
        try:
            await asyncio.wait_for(_model_sem.acquire(), timeout=MAX_QUEUE_WAIT)
        except asyncio.TimeoutError:
            _log_call(route, user, "queued", t0)
            return "queued", _queue_reply(lang), _waiting
    finally:
        _waiting -= 1
    try:
        try:
            reply = await _call_ollama(message, lang, image_base64, kiosk)
            outcome = "ok"
        except ModelFailure as failure:
            reply, outcome = None, failure.outcome
    finally:
        _model_sem.release()
    _log_call(route, user, outcome, t0)
    if outcome == "ok":
        return "ok", reply, None
    if outcome == "timeout":
        return "timeout", _timeout_reply(lang), None
    return "fallback", _stub_reply(lang), None


def _kiosk_problem(user: str, kiosk: str):
    """Return an error response when the kiosk name is unknown or not this key's own, else None."""
    if kiosk not in PROMPTS:
        return JSONResponse(status_code=400, content={"error": f"Unknown kiosk. Use one of: {', '.join(sorted(PROMPTS))}."})
    if user.startswith("app:") and user != f"app:{kiosk}":
        return JSONResponse(status_code=403, content={"error": "This key belongs to another kiosk."})
    return None


def _response(status: str, reply: str, lang: str, queue_position=None, extra=None):
    answered = status in ("ok", "timeout")  # on a timeout the model is connected, only slow
    body = {
        "reply": reply,
        "stub": not answered,
        "ollama_available": answered,
        "model": OLLAMA_MODEL if answered else "not-connected",
    }
    if status == "queued":
        body["queue_position"] = queue_position
    if status == "timeout":
        body["timeout"] = True
    if extra:
        body.update(extra)
    code = {"queued": 503, "timeout": 504}.get(status, 200)
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
async def chat(request: Request):
    user, denied = _require_key(request, allow_app=True)
    if denied:
        return denied
    try:
        req = ChatRequest(**(await request.json()))
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Body must be JSON with a message."})
    if len(req.message) > MAX_QUESTION_CHARS:
        return JSONResponse(status_code=413, content={"error": f"Question over {MAX_QUESTION_CHARS} characters."})
    problem = _kiosk_problem(user, req.kiosk)
    if problem:
        return problem
    status, reply, queue_pos = await _guarded_model_call(
        req.message, req.lang, req.image_base64, "chat", user, req.kiosk
    )
    return _response(status, reply, req.lang, queue_pos)


@app.post("/api/vision")
async def vision(request: Request):
    """Accept a base64 image (JSON) or a file upload (multipart).

    JSON: {"message", "lang", "image_base64"}. Multipart: file field
    named "image" (or "file"), plus optional "message"/"lang" fields.
    The image is used for this one answer only and is never stored.
    """
    user, denied = _require_key(request, allow_app=True)
    if denied:
        return denied
    content_type = request.headers.get("content-type", "")
    message = "Lee este documento y explícalo en español."
    lang = "es"
    kiosk = DEFAULT_KIOSK
    image_b64: str | None = None
    filename = None
    n_bytes = 0

    if "multipart/form-data" in content_type:
        form = await request.form()
        message = str(form.get("message") or message)
        lang = str(form.get("lang") or lang)
        kiosk = str(form.get("kiosk") or kiosk)
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
        kiosk = str(body.get("kiosk") or kiosk)
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

    if len(message) > MAX_QUESTION_CHARS:
        return JSONResponse(status_code=413, content={"error": f"Question over {MAX_QUESTION_CHARS} characters."})
    problem = _kiosk_problem(user, kiosk)
    if problem:
        return problem
    status, reply, queue_pos = await _guarded_model_call(message, lang, image_b64, "vision", user, kiosk)
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
async def _no_stale_pages(request: Request, call_next):
    """A browser must never keep the old page after a deploy. Cloudflare overrides
    "no-cache" with max-age=14400 (4 hours) for .js/.css files, but it honors
    "no-store" (checked live, 2026-11-08). The files are small, so no caching is fine."""
    response = await call_next(request)
    path = request.url.path
    if (path.startswith("/apps/") or path.startswith("/packages/")) and "cache-control" not in response.headers:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.middleware("http")
async def _limit_body_size(request: Request, call_next):
    """Refuse big or length-less POST bodies before anything reads them (an 8 GB board has no room)."""
    path = request.url.path
    if request.method == "POST" and (path.startswith("/api/") or path.startswith("/v1/")):
        length = request.headers.get("content-length")
        if length is None:
            return JSONResponse(status_code=411, content={"error": "Content-Length is required."})
        if not length.isdigit():
            return JSONResponse(status_code=400, content={"error": "Bad Content-Length."})
        if int(length) > MAX_BODY_BYTES:
            return JSONResponse(status_code=413, content={"error": f"Body over {MAX_BODY_BYTES // 1_000_000} MB."})
    return await call_next(request)


@app.middleware("http")
async def _app_only_hosts(request: Request, call_next):
    host = request.headers.get("host", "").split(":")[0].lower()
    if request.url.path.startswith("/v1") and host in APP_ONLY_HOSTS:
        return JSONResponse(status_code=404, content={"error": {"message": "Not found."}})
    return await call_next(request)


# ---- Keys: every route that reaches the model needs one ------------------
# Users are names in api-keys.json. People and agents have plain names.
# Apps are service users named "app:<kiosk>" (spec 22). A page is public,
# so an app key is an identity tag, not a secret: it works on /api/* only
# and is refused on /v1/*.


def _load_keys() -> dict:
    try:
        with open(API_KEYS_FILE) as f:
            keys = json.load(f)
    except (OSError, ValueError):
        return {}  # no key file means no keys: the API stays closed
    return keys if isinstance(keys, dict) else {}


def _presented_key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    return auth[7:] if auth.lower().startswith("bearer ") else request.headers.get("x-api-key", "")


def _api_user(request: Request) -> str | None:
    """Name of the user whose key the request carries, or None."""
    key = _presented_key(request)
    found = None
    for name, k in _load_keys().items():
        if key and hmac.compare_digest(str(k), key):
            found = name
    return found


def _unauthorized() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"error": {"message": "Missing or invalid API key. Send Authorization: Bearer <key>.", "type": "invalid_api_key"}},
    )


def _require_key(request: Request, allow_app: bool):
    """Return (user, None) if the key is good, else (None, the error response)."""
    user = _api_user(request)
    if not user:
        why = "bad_key" if _presented_key(request) else "missing"
        print(f"refused path={request.url.path} why={why}", flush=True)  # never the key itself
        return None, _unauthorized()
    if user.startswith("app:") and not allow_app:
        print(f"refused path={request.url.path} why=app_key_on_v1", flush=True)
        return None, JSONResponse(
            status_code=403,
            content={"error": {"message": "This key is not allowed here.", "type": "key_not_allowed"}},
        )
    return user, None


@app.get("/apps/{kiosk}/config.js", include_in_schema=False)
async def app_config(kiosk: str):
    """Give a kiosk page its own key. Only app:<name> keys are ever served."""
    key = _load_keys().get("app:" + kiosk.removeprefix("kiosk-"))
    if not key:
        return Response(status_code=404)
    return Response(
        content=f"window.KIOSK_CONFIG = {json.dumps({'apiKey': key})};\n",
        media_type="application/javascript",
        headers={"Cache-Control": "no-store"},
    )


# ---- Team API: OpenAI-compatible -----------------------------------------


@app.get("/v1/models")
async def v1_models(request: Request):
    _, denied = _require_key(request, allow_app=False)
    if denied:
        return denied
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            r = await client.get(f"{OLLAMA_HOST}/v1/models")
        return Response(content=r.content, status_code=r.status_code, media_type="application/json")
    except Exception:
        return JSONResponse(status_code=502, content={"error": {"message": "Ollama is not reachable."}})


@app.post("/v1/chat/completions")
async def v1_chat(request: Request):
    """Pass-through to Ollama's OpenAI-compatible API: text and images, any installed model."""
    user, denied = _require_key(request, allow_app=False)
    if denied:
        return denied
    try:
        body = await request.json()
    except Exception:
        body = None
    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={"error": {"message": "Body must be a JSON object."}})
    if body.get("stream"):
        return JSONResponse(status_code=400, content={"error": {"message": "stream is not supported; send stream:false."}})
    body.setdefault("model", OLLAMA_MODEL)
    t0 = time.monotonic()
    try:
        await asyncio.wait_for(_model_sem.acquire(), timeout=MAX_QUEUE_WAIT)
    except asyncio.TimeoutError:
        _log_call("v1", user, "queued", t0, str(body["model"]))
        return JSONResponse(status_code=503, content={"error": {"message": "The model is busy. Try again in a moment."}})
    outcome = "ok"
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT, trust_env=False) as client:
            r = await client.post(f"{OLLAMA_HOST}/v1/chat/completions", json=body)
        if r.status_code != 200:
            outcome = "error"
        return Response(content=r.content, status_code=r.status_code, media_type="application/json")
    except httpx.TimeoutException as e:
        outcome = "timeout"
        _log_error(e)
        return JSONResponse(status_code=504, content={"error": {"message": "The model took too long. Try again."}})
    except Exception as e:
        outcome = "unreachable"
        _log_error(e)
        return JSONResponse(status_code=502, content={"error": {"message": "Ollama is not reachable."}})
    finally:
        _model_sem.release()
        _log_call("v1", user, outcome, t0, str(body["model"]))


@app.get("/", include_in_schema=False)
async def root(request: Request):
    query = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(f"/apps/launcher/{query}")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """A tent with a spark: browsers ask for this path without being told."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "packages", "shared-ui", "favicon.svg")
    with open(path, "rb") as f:
        body = f.read()
    return Response(body, media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


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
