# AI Kiosk

Local AI kiosks on Jetson: one box, one agent, all inference on-device.
Nothing leaves the box.

## The three kiosks

| Kiosk | Who it serves | What the agent sees (PiP) | Status |
| --- | --- | --- | --- |
| [Intercambio](apps/kiosk-intercambio/) | Spanish-speaking newcomers at a community center | Camera, pointed at a document | Prototype — building first |
| [Shop Operator](apps/kiosk-shop/) | Small shops running legacy Windows software | Screenshot of the shop's Windows PC | Stub — phase 2 |
| [Nonprofit](apps/kiosk-nonprofit/) | Small nonprofits in Boulder County | Camera, pointed at a document | Stub — phase 2 |

## Layout

```
Visitor (kiosk) / remote tester (browser, ?mode=remote)
  │  remote testers arrive via a Cloudflare Tunnel to the Jetson
  ▼
Web UI (apps/kiosk-*) — Agent main view + Picture-in-Picture
  │  kiosk: live webcam in the PiP · remote: upload-a-photo in the PiP
  ▼
FastAPI backend (services/agent-backend/)
  │  wired to Ollama on localhost:11434 — Qwen3-VL 4B
  │  honest stub fallback if Ollama is down · max 2 concurrent calls
  ▼
Cloudflare Tunnel (optional, remote only) — backend on :8000 only,
Ollama on :11434 is never tunnelled. See docs/remote-access.md.
```

```
apps/
  kiosk-intercambio/   # first working prototype: agent + Picture-in-Picture
  kiosk-shop/          # stub
  kiosk-nonprofit/     # stub
  website/             # static landing page for the project
services/
  agent-backend/       # FastAPI, wired to Ollama (see its README)
packages/
  shared-ui/           # PiP + agent-view styles shared by all kiosks
hardware/
  jetson/              # Jetson Orin Nano Super setup notes + cloudflared/
docs/
  architecture.md      # how the pieces fit
  plan-intercambio.md  # Intercambio first: scope and rules
  remote-access.md     # Cloudflare Tunnel to the Jetson
  agent-visual-roadmap.md  # agent face: waveform (built) → mascot → face avatar
```

## Run the Intercambio prototype

Serve the **repo root** (the kiosk pages link to the shared styles in
`packages/shared-ui/` via relative paths), then open the app:

```bash
python3 -m http.server 8000
# open http://localhost:8000/apps/kiosk-intercambio/
# remote testers: .../apps/kiosk-intercambio/?mode=remote  (upload-a-photo, no camera)
```

No build step, no framework, no install. Any plain static server works.
With the backend running (`services/agent-backend/`, Ollama on
`localhost:11434`), the app's replies come from Qwen3-VL 4B; without
it, the app falls back to an honestly-labelled demo reply. The
backend can also serve the UI itself on port 8000 — that is the mode
the Cloudflare Tunnel uses (one origin, UI + API together).

## Rules that do not change

- **Local first.** The model runs on the Jetson in the box. No cloud
  account, no tracking, no recording.
- **The visitor sees what the agent sees.** The Picture-in-Picture window
  is always available; it is live only, never stored.
- **Bilingual, Spanish-first** for Intercambio. The agent helps people
  read, explain, and translate forms and navigate local services. It is
  navigation, not legal advice.
- **Honest demos.** A stub says it is a stub. Nothing pretends the model
  answered when it did not.

## Hardware (pilot unit)

Jetson Orin Nano Super Developer Kit, 8 GB. Setup notes in
[`hardware/jetson/README.md`](hardware/jetson/README.md).
