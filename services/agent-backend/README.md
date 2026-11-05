# agent-backend

Python FastAPI service that runs on the Jetson, next to the kiosk web
app. The front end talks to it over `http://localhost:8001` (same box,
never the internet).

## Current state: skeleton with stubs

- `GET /health` — `{"status": "ok", "stub": true, "model": "not-connected"}`
- `POST /api/chat` — `{"message", "lang"}` → canned reply, marked `stub: true`
- `POST /api/vision` — multipart image upload (the frozen PiP frame) →
  canned description, marked `stub: true`

The stubs exist so the front end can be wired and tested before the
model is installed. They say they are stubs; nothing pretends to be
the model.

## How it will connect (Saturday)

1. Install llama.cpp (CUDA build) or Ollama on the Jetson.
2. Download **Qwen3-VL 4B** (Apache 2.0, ~3.3 GB) — the one brain for
   conversation + vision. Qwen3-VL 8B (~6.1 GB Q4) is the later,
   tighter upgrade, not the first step.
3. Point `/api/chat` and `/api/vision` at the local model server.
   Both endpoints keep the same request/response shape, so the kiosk
   front end does not change.
4. Voice: Whisper for speech-to-text, Piper for text-to-speech, both
   local. (The prototype front end uses the browser Web Speech API
   as a stand-in; the backend replaces it on-device.)

## Run it (stub mode)

```bash
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8001
curl http://127.0.0.1:8001/health
```

## Model config (planned)

| Setting | Value |
| --- | --- |
| Model | Qwen3-VL 4B (Q4_K_M via llama.cpp, or `qwen3-vl:4b` via Ollama) |
| Context | ~4K practical on the 8 GB Jetson (not the 262K family max) |
| Language | Spanish-first, English second |
| License | Apache 2.0 |

**Not used:** TwIL-8B — text-only, English-only, non-commercial
license. Wrong tool for a bilingual vision kiosk.
