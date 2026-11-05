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
apps/
  kiosk-intercambio/   # first working prototype: agent + Picture-in-Picture
  kiosk-shop/          # stub
  kiosk-nonprofit/     # stub
  website/             # static landing page for the project
services/
  agent-backend/       # Python FastAPI skeleton (stubs for now)
packages/
  shared-ui/           # PiP + agent-view styles shared by all kiosks
hardware/
  jetson/              # Jetson Orin Nano Super setup notes
docs/
  architecture.md      # how the pieces fit
  plan-intercambio.md  # Intercambio first: scope and rules
```

## Run the Intercambio prototype

Serve the **repo root** (the kiosk pages link to the shared styles in
`packages/shared-ui/` via relative paths), then open the app:

```bash
python3 -m http.server 8000
# open http://localhost:8000/apps/kiosk-intercambio/
```

No build step, no framework, no install. Any plain static server works.

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
