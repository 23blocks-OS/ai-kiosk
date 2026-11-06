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

## Authenticated identity — Auth API device flow (available 2026-11-06)

Where an authenticated identity is actually needed (for example
registering the Jetson itself, or a future remote-access path that
must know who is calling), the 23blocks Auth API now ships the
**OAuth 2.0 Device Authorization Grant (RFC 8628)** — live
v4.52.12 at `https://auth.api.us.23blocks.com` (repo
`23blocks/blocks-auth-api`, issue #113, PRs #123–125). It fits a
kiosk exactly: the Jetson shows a short code on its screen
(`ABCD-1234` format) and approval happens on a phone — no keyboard,
no pasted secrets.

- Device asks: `POST /device/authorize` with the company API key
  (`X-API-KEY` header), optional `client_id` and `scope`. Returns
  `device_code`, `user_code`, `verification_uri` and
  `verification_uri_complete`. Codes live 10 minutes, poll every
  5 seconds.
- User approves: opens the verification URI on their phone, logs
  in, enters the code, approves or denies.
  `POST /apps/:app_url_id/device/verify` with the user's Bearer
  JWT, `user_code` + `action_type` (approve/deny). Approval checks
  the user holds the requested scopes.
- Device polls: `POST /:company_url_id/oauth/token` with
  `grant_type=urn:ietf:params:oauth:grant-type:device_code` and the
  `device_code`. Answers: `authorization_pending`, `slow_down`
  (polling too fast, +5 s penalty), `access_denied`, `expired_token`.
- On approval: a 5-minute RS256 Bearer token, single-use, default
  scope `devices:register`. The code is then consumed.
- Rate limits: 20/IP/10 min, 30/key/10 min. The company API key
  stays server-side on the Jetson; it is never in the repo or in
  the browser.

**Scope guard (standing):** the Intercambio kiosk is no-account,
data never leaves the box. This flow is for the *device / operator*
identity where one is actually needed — it does **not** add accounts
or sign-ins to the visitor flow. Visitors still walk up, tap, and
talk, with nothing to log into.

**Two gaps, open:**
- The verification page is **not built** (`DEVICE_VERIFICATION_URI`
  env; the API code says "not built yet"). Either build it, or call
  the verify endpoint from an existing logged-in frontend.
- The feature flag (`DEVICE_FLOW_ENABLED=true`) is unconfirmed in
  production from outside: the endpoint is live — re-verified
  2026-11-06, `POST /device/authorize` answers 401 without a key,
  not a routing 404 — but the first real call with a company API
  key settles it.
