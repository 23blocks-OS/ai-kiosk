# Kiosk — Intercambio

The first working kiosk: a bilingual helper for Spanish-speaking newcomers
at a community center. It reads a form or letter placed under the camera
and explains it, translates it, and helps with the next step.

## What it is

- **Agent (main view):** conversation, big ES/EN toggle (Spanish by
  default), big mic button, text input. Status is always visible:
  Idle / Listening / Thinking / Speaking.
- **Picture-in-Picture (bottom-right):** live webcam feed, labelled
  "Lo que estoy viendo / What I'm seeing". Tap to expand, freeze a frame
  (the snapshot the agent would analyze), hide it and bring it back.

## What it is not (yet)

The replies in this prototype are canned and say so: *"Esto es una
demostración: todavía no estoy conectado al modelo local."* Nothing here
pretends the AI answered. The local model (Qwen3-VL 4B on the Jetson)
connects through `services/agent-backend/` — see `docs/architecture.md`.

## Rules

- Bilingual, Spanish-first. Navigation help, not legal advice.
- No account, no tracking, no recording. Nothing leaves the device.
- The camera starts only when the visitor taps "Activar cámara". If
  permission is denied, the app says so plainly and the text box still works.
- Voice uses the browser's Web Speech API when available; when it is not,
  the app says so and the text box is the way in.

## Run it

Serve the **repo root** and open the app (shared styles live in
`packages/shared-ui/`):

```bash
python3 -m http.server 8000
# http://localhost:8000/apps/kiosk-intercambio/
```

## Saturday test (Jetson)

1. Boot the Jetson, open this page in full-screen Chromium kiosk mode.
2. Plug in the USB webcam, tap "Activar cámara", put a sample form under it.
3. Check the PiP shows the document clearly and Freeze captures a readable frame.
4. Then connect the backend: Qwen3-VL 4B reads the frozen frame and
   replaces the canned reply.
