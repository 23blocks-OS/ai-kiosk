# Architecture

```
Visitor
  │
  ▼
Web UI — full-screen Chromium kiosk mode (apps/kiosk-*)
  │  no build step, no framework, plain HTML/CSS/JS
  │  served from the repo root on the Jetson
  ▼
Local Python backend — FastAPI (services/agent-backend/)
  │  http://127.0.0.1:8001, same box only
  ▼
Qwen3-VL 4B — one vision-language model (llama.cpp / Ollama)
  │  conversation + vision in one model, Apache 2.0
  ▼
Whisper (speech-to-text) + Piper (text-to-speech), both local
```

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
   ES/EN toggle. Shared styles: `packages/shared-ui/agent.css`.
2. **Picture-in-Picture (bottom-right, ~25–30% width).** What the
   agent is seeing, live. Tap to expand, freeze a frame (the snapshot
   the agent analyzes), hide it and bring it back. Shared styles:
   `packages/shared-ui/pip.css`.

PiP source by kiosk:

| Kiosk | PiP source |
| --- | --- |
| Intercambio | USB webcam, pointed at a document |
| Shop Operator | Live screenshot of the shop's Windows PC |
| Nonprofit | USB webcam, pointed at a document |

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
| Intercambio front end | Working prototype (canned replies, honestly labelled) |
| Shop / Nonprofit front ends | Placeholder pages reusing the shell |
| agent-backend `/health`, `/api/chat`, `/api/vision` | Stubs returning canned replies |
| Qwen3-VL 4B on the Jetson | Not installed yet — Saturday |
| Whisper + Piper on the Jetson | Not installed yet — Saturday |
| Website | Static page, real copy |
