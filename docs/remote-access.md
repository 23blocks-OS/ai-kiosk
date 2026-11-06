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

## Authenticated identity — Auth API device flow (NOT live yet, 2026-11-06)

Where an authenticated identity is actually needed (for example
registering the Jetson itself, or a future remote-access path that
must know who is calling), the **OAuth 2.0 Device Authorization
Grant (RFC 8628)** is the design — code merged to
`23blocks/blocks-auth-api` development only (issue #113, PRs
#123–125). It is **not in the deployed build yet**: the live probe
at 14:03 MST on v4.52.12 returned 404 for the route, and the 401
seen without a key proves only that the auth middleware is alive,
not that the route exists. At 14:58 MST `/health` reported v6.1.2,
so a deploy happened in between — but the route is still unproven
without a company API key. The decisive test is
`POST /device/authorize` via the Operario proxy with the
publishable key: a 200 with codes settles it. (Correction: earlier
notes in this repo called the flow "live" — that was wrong.)

Once deployed, the flow is:
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
- Deploy + env: the Auth API code must be deployed, then
  `DEVICE_FLOW_ENABLED=true` and
  `DEVICE_VERIFICATION_URI=https://app.operario.tech/device` set.
  Do NOT deploy without Juan's word (normal flow: PR → development
  → staging → tag → production). Operario issues #13/#14 stay open
  until the live probe passes.
- Verification page: the Auth API's own page is still not built —
  but the Operario side is DONE 2026-11-06 (PR #18, commit
  6e7e1a1): the server proxies the flow holding the company key,
  `GET /device` is the console approval page, and the installers
  sign in through it. So the kiosk path would use the Operario
  console page, not the Auth API's.
