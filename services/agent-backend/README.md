# agent-backend

Python FastAPI service that runs on the Jetson, next to the kiosk web
app. The front end talks to it over HTTP; the backend talks to Ollama
on the same box. Nothing here calls a cloud service.

## How it connects

```
kiosk UI -> this backend -> Ollama http://localhost:11434
                            model: qwen3-vl:4b (Qwen3-VL 4B, ~3.3 GB)
```

- `GET /health` — `{"status": "ok", "stub": <bool>, "model": ..., "ollama_available": <bool>}`. It probes Ollama (`GET /api/tags`, 2 s timeout) on every call.
- `POST /api/chat` — `{"message", "lang", "image_base64"?}` → the model's reply, or the honest stub if Ollama is down.
- `POST /api/vision` — JSON `{"message", "lang", "image_base64"}` **or** multipart with an image file (`image`/`file` field) plus optional `message`/`lang` fields → the model's description of the image. The image is used for that one answer only and is never stored.

Both AI endpoints share one system prompt (in `main.py`): bilingual,
Spanish-first Intercambio helper — read/explain/translate forms,
navigate local services, **not legal advice**.

## Honest fallback (do not remove)

If Ollama is unreachable, errors, or times out, the endpoints return
the canned demo reply with `"stub": true` and
`"ollama_available": false`, and `/health` reports the same. They
never fake a model answer. The front end shows that reply as-is.

## Concurrency guard

At most `MAX_CONCURRENT_MODEL_CALLS` (default **2**) model calls run
at once (asyncio semaphore). 1 user = full speed, 2 = about half
speed each, a 3rd waits in line. If it would wait longer than
`MAX_QUEUE_WAIT_SECONDS` (default 30 s), it gets HTTP 503 with a
plain-language reply in ES/EN — "Hay 2 personas usando el agente
ahora mismo, eres el siguiente en la fila" — plus `queue_position`.
The 8 GB Jetson shares one GPU; that is the limit, not the web server.

## Config (environment only, no secrets)

Copy `.env.example` to `.env` if you want to change the defaults:

| Variable | Default | Meaning |
| --- | --- | --- |
| `OLLAMA_HOST` | `http://localhost:11434` | Where Ollama listens (same box) |
| `OLLAMA_MODEL` | `qwen3-vl:4b` | Model name in Ollama |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | Max wait for one model reply |
| `MAX_CONCURRENT_MODEL_CALLS` | `2` | Model calls running at once |
| `MAX_QUEUE_WAIT_SECONDS` | `30` | Max queue wait before HTTP 503 |

## Run it on the Jetson (Saturday)

```bash
# 1. Install Ollama and pull the model (once)
ollama pull qwen3-vl:4b

# 2. Local dev (kiosk UI served by a static server on :8000)
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8001
curl http://127.0.0.1:8001/health

# 3. Tunnel mode (one origin: the backend serves the UI too, on :8000)
uvicorn main:app --host 127.0.0.1 --port 8000
# then: cloudflared tunnel run ai-kiosk   (see hardware/jetson/cloudflared/)
```

## Model config

| Setting | Value |
| --- | --- |
| Model | Qwen3-VL 4B (`qwen3-vl:4b` via Ollama) |
| Context | ~4K practical on the 8 GB Jetson (not the 262K family max) |
| Language | Spanish-first, English second |
| License | Apache 2.0 |

**Not used:** TwIL-8B — text-only, English-only, non-commercial
license. Wrong tool for a bilingual vision kiosk. Voice (Whisper +
Piper, both local) is not wired into the backend yet — the prototype
front end uses the browser Web Speech API as a stand-in.
