# Remote access — Cloudflare Tunnel to the Jetson

**Route decided 2026-11-05:** remote testers reach the *same* agent
on the *same* Jetson through a Cloudflare Tunnel. Not a cloud copy of
the agent, not a second model in the cloud.

## Why this is the selling point

- **Same box, same agent.** The person online talks to the exact
  Jetson and the exact local model (Qwen3-VL 4B) as the person
  standing at the kiosk. A cloud copy would prove nothing about
  small, local AI.
- **No cloud GPU bill.** The model still runs on the Jetson.
  Cloudflare Tunnel is free; Cloudflare is only the front door.
- **No open ports, no public IP.** `cloudflared` on the Jetson dials
  *out* to Cloudflare. Nothing listens on the public internet, and
  nobody can reach into the home / community-center network.
- **Privacy story stays true.** The document is processed on the
  Jetson, not sent to OpenAI or any cloud model. It travels
  encrypted through the tunnel to get there, and it is not stored.

## How it works

```
Remote tester (browser, anywhere)
  │  https://kiosk.ciaocorp.com
  ▼
Cloudflare edge (TLS, DDoS protection, optional Access login)
  │  outbound-only tunnel, no open ports
  ▼
cloudflared on the Jetson (ARM64)
  │  http://localhost:8000 — the backend ONLY
  ▼
agent-backend (FastAPI, serves the kiosk UI + /api/*)
  │  http://localhost:11434 — same box only
  ▼
Ollama — Qwen3-VL 4B
```

**The tunnel points ONLY at the backend on `localhost:8000`.**
Ollama on port 11434 is never tunnelled and never exposed. The
backend serves the kiosk UI itself from that port (it mounts the
repo's static files), so remote testers use one origin and one
`https://` link — no second port, no CORS.

Remote PiP: there is no webcam to point at a document online, so the
PiP becomes **upload-a-photo** (`?mode=remote` in the Intercambio
app). The photo is downscaled in the browser to 1024 px, sent to
`/api/vision`, used for that one answer, and not saved.

## Limits, stated honestly

- **The Jetson must be on and online.** If it is off, the link is dead.
- **Home upload bandwidth is the ceiling.** The Jetson answers over
  the connection it sits on.
- **Concurrency is the 8 GB limit, not a Cloudflare limit:** 1 user
  gets full speed, 2 get about half each, a 3rd waits in line and
  gets a 503 "you're next" reply after 30 s queued. See
  `services/agent-backend/README.md`.
- **One Jetson = one tunnel.** A second kiosk needs its own tunnel
  and subdomain.

## Setup

See `hardware/jetson/cloudflared/README.md` for the Saturday steps:
install `cloudflared`, `cloudflared tunnel login`, create the tunnel,
add the Public Hostname in the Cloudflare Zero Trust dashboard, run
the tunnel, verify the `https://` link. The hostname is
**https://kiosk.ciaocorp.com** (decided 2026-11-05) — a single-level
subdomain, covered by Cloudflare's free Universal SSL wildcard for
`*.ciaocorp.com` (unlike the two-level `shop.demo.ciaocorp.com`,
which could never get a certificate).

To restrict testers later, add **Cloudflare Access** (Zero Trust) on
the same hostname: allow only listed email addresses. No code change
is needed for that.
