# Architecture

```
Visitor (kiosk) / remote tester (browser, ?mode=remote)
  │
  ▼
Web UI — full-screen Chromium kiosk mode (apps/kiosk-*)
  │  no build step, no framework, plain HTML/CSS/JS
  │  served from the repo root on the Jetson
  ▼
Local Python backend — FastAPI (services/agent-backend/)
  │  http://127.0.0.1:8001 in local dev; port 8000 when served
  │  through the Cloudflare Tunnel (one origin, UI + API together)
  ▼
Ollama — Qwen3-VL 4B (http://localhost:11434, same box only)
  │  conversation + vision in one model, Apache 2.0
  ▼
Whisper (speech-to-text) + Piper (text-to-speech), both local
```

Remote testers reach the same backend through a Cloudflare Tunnel
(`docs/remote-access.md`): `cloudflared` on the Jetson dials out to
Cloudflare, no open ports, and the tunnel points ONLY at the backend
on `localhost:8000`. Ollama on 11434 is never tunnelled.

## Why a web UI

The kiosk screen is a web page opened full-screen. It is the fastest
thing to build and change, and the same code can later be wrapped
(Electron / Tauri) without a rewrite. A native Qt/GTK app would be
slower to build and harder to update across several kiosks.

The web page does no AI itself. All inference happens in the backend
on the same Jetson.

## The two screen elements

1. **Agent (main view).** Status (Idle / Listening / Thinking /
   Speaking), conversation transcript, big mic button, text input,
   ES/EN toggle. The agent's face is Phase 1: an animated
   waveform/orb (`docs/agent-visual-roadmap.md`) — it breathes when
   idle, ripples when listening, spins while thinking, moves while
   speaking, and glances at the PiP while reading a document.
   Shared styles: `packages/shared-ui/agent.css`.
2. **Picture-in-Picture (bottom-right, ~25–30% width).** What the
   agent is seeing, live. Tap to expand, freeze a frame (the snapshot
   the agent analyzes), hide it and bring it back. Shared styles:
   `packages/shared-ui/pip.css`.

PiP source by kiosk:

| Kiosk | PiP source |
| --- | --- |
| Intercambio | USB webcam, pointed at a document — or, remote (`?mode=remote`), an uploaded photo of the document |
| Shop Operator | Live screenshot of the shop's Windows PC |
| Nonprofit | USB webcam, pointed at a document |

## Concurrency (8 GB Jetson)

The backend allows at most **2 concurrent model calls** (asyncio
semaphore, `MAX_CONCURRENT_MODEL_CALLS`). 1 user gets full speed, 2
get about half each, and a 3rd waits in line — after 30 s queued
(`MAX_QUEUE_WAIT_SECONDS`) it gets HTTP 503 with a plain-language
"you're next in line" reply in ES/EN. The model is one GPU shared by
everyone; the web server itself is not the bottleneck.

## The model: one brain, not two

**Qwen3-VL 4B** (Apache 2.0, ~3.3 GB) does conversation and vision in
one model: it reads a form (OCR), explains it in Spanish or English,
and chats about it. Qwen3-VL 8B (~6.1 GB Q4) is the later, tighter
upgrade. Do not run a separate chat LLM plus a separate VLM at the
same time on the 8 GB board — they fight over RAM.

Moondream 2 (~2 B) is a specialist helper for finding UI elements on
a screen (Shop Operator), not the main chat model.

**Not used: TwIL-8B.** Text-only, English-only, and under the webAI
Non-Commercial License 1.0 — it cannot be used commercially as-is, and
it cannot see a document. Its Apache 2.0 base, Granite 4.2 8B, is a
fine deployable text baseline if a text-only model is ever needed.

## Privacy

- All inference on-device. No cloud account, no API key, no network
  call to any model provider.
- The camera starts only on a user tap. The PiP is live only — nothing
  is recorded or stored. When a session ends, the PiP goes dark.
- Screenshots of a shop's screen stay on the Jetson in the shop.
- The kiosk has no user accounts and no tracking.

## What is a stub, and what is real

| Piece | State |
| --- | --- |
| Intercambio front end | Working prototype, now calls the backend (Ollama when up, honest stub when not); remote upload mode (`?mode=remote`); animated waveform/orb agent visual (Phase 1, `docs/agent-visual-roadmap.md`) |
| Shop / Nonprofit front ends | Placeholder pages reusing the shell |
| agent-backend `/health`, `/api/chat`, `/api/vision` | Wired to Ollama (Qwen3-VL 4B); honest stub fallback when Ollama is down; concurrency guard of 2 |
| Cloudflare Tunnel | Docs + config only (`docs/remote-access.md`, `hardware/jetson/cloudflared/`) — not run yet, no token, no subdomain chosen |
| Qwen3-VL 4B on the Jetson | Not installed yet — Saturday |
| Whisper + Piper on the Jetson | Not installed yet — Saturday |
| Website | Static page, real copy |
