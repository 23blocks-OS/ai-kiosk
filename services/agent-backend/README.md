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
| `OLLAMA_TIMEOUT_SECONDS` | `90` | Max wait for one model reply. Keep it under Cloudflare's tunnel limit (about 100 s), so the backend answers first. |
| `MAX_CONCURRENT_MODEL_CALLS` | `2` | Model calls running at once |
| `MAX_QUEUE_WAIT_SECONDS` | `30` | Max queue wait before HTTP 503 |
| `MAX_BODY_MB` | `8` | Biggest `POST` body for `/api/*` and `/v1/*`. Over it: 413. No `Content-Length`: 411. A question over 4,000 characters: 413. |

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

## Team API (`/v1/*`): OpenAI-compatible, API key required

For people and agents, on the Cloudflare Tunnel and on the tailnet. Same rule everywhere: every call needs a key.

- `GET /v1/models` lists the models installed in Ollama.
- `POST /v1/chat/completions` passes the request to Ollama (text and images, any installed model). `stream` is not supported. It shares the 2-call limit with the kiosk.
- Send `Authorization: Bearer <key>` (or `X-API-Key: <key>`).

```bash
curl https://aureliano.twofourai.com/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"qwen3-vl:4b","messages":[{"role":"user","content":"Hello"}]}'
```

**Users and keys** live in `services/agent-backend/api-keys.json`: `{"name": "key", ...}`. The file is read on every request, so edits apply at once. It is in `.gitignore` and never goes to GitHub; `api-keys.example.json` shows the shape. Add a user: `openssl rand -hex 24`, then add the line. Remove a user: delete the line. No file means the API is closed.

**Every route that reaches the model needs a key**, including the kiosk page's own `/api/chat` and `/api/vision`. Only `/health` and the page files are open.

**Apps are service users.** An app is a name in `api-keys.json` like `app:intercambio` (the kiosk folder `kiosk-intercambio` maps to `app:intercambio`). The server hands each page its key at `/apps/<kiosk>/config.js` (never from git, `Cache-Control: no-store`), and the page sends it as `Authorization: Bearer`.

| Key | `/api/*` (kiosk routes) | `/v1/*` (team API) |
| --- | --- | --- |
| Person or agent (`alice`) | yes | yes |
| App (`app:intercambio`) | yes | **no, 403** |

**A page is public, so an app key is an identity tag, not a secret.** Anyone who opens the kiosk can read it. It gives you named logs (`api user=app:intercambio`) and per-app revoke and rotate. It does not stop abuse of `/api/*`: see issues #8 and #9. It must never work on `/v1/*`, or every visitor would get the team API.

To add a kiosk: `openssl rand -hex 24`, add `"app:<name>": "<key>"` to `api-keys.json`, and load `config.js` before `app.js` in its page. To rotate: edit the file; pages pick the new key on the next load. No file or no `app:` line means the page gets a 404 for `config.js` and shows "this app is not authorized".

Local dev: run the backend (not a plain static server) with an `api-keys.json` that has an `app:intercambio` line.

**App-only hostnames.** `APP_ONLY_HOSTS=kiosk.ciaocorp.com` makes `/v1/*` a 404 on that hostname, even with a valid key. The team hostname (`aureliano.twofourai.com`) and the tailnet keep both the app and the API.


## Honest outcomes and the call log

Each model call ends in one outcome:

| Outcome | Visitor sees | HTTP |
| --- | --- | --- |
| `ok` | The model's reply | 200 |
| `timeout` | "The agent is taking longer than usual. Please try again." (`timeout: true`, `stub: false`: the model is connected, only slow) | 504 |
| `queued` | "You're next in line" | 503 |
| `unreachable`, `error`, `empty` | The labelled stub (`stub: true`) | 200 |

The model stays loaded (`keep_alive: -1`), and the backend loads it at startup, so the first visitor is not the one who waits. Ollama still swaps it out if a team caller asks for another model.

**Log** (`journalctl --user -u ai-kiosk`). One line per call, never the question, the answer, an image, a visitor address or a key:

```
call route=chat user=app:intercambio outcome=ok ms=5120 model=qwen3-vl:4b-instruct
model_error reason=ReadTimeout
refused path=/api/chat why=bad_key        (missing | bad_key | app_key_on_v1)
warmup model=qwen3-vl:4b-instruct outcome=ok
```
