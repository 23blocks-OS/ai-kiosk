# Cloudflare Tunnel on the Jetson

Remote testers reach the *same* Jetson agent through a Cloudflare
Tunnel — see `docs/remote-access.md` for why. This folder holds only
config and setup steps. **No tunnel runs in this repo, no token lives
here. The hostname is https://kiosk.ciaocorp.com** (decided
2026-11-05, single-level subdomain, covered by Cloudflare's free
Universal SSL wildcard).

## Saturday steps (on the Jetson, after it boots and Ollama works)

1. Install cloudflared:
   ```bash
   ./install-cloudflared.sh
   ```
   It installs the ARM64 `.deb` only. It refuses to run if you pass
   it a token — tokens are never typed into a script.
2. Log in (opens a browser, pick the Cloudflare account):
   ```bash
   cloudflared tunnel login
   ```
3. Create the tunnel:
   ```bash
   cloudflared tunnel create ai-kiosk
   ```
   Note the tunnel id it prints.
4. Copy the example config and fill in your own values:
   ```bash
   mkdir -p ~/.cloudflared
   cp config.yml.example ~/.cloudflared/config.yml
   # edit: TUNNEL-ID-PLACEHOLDER -> your tunnel id
   #       hostname is already kiosk.ciaocorp.com
   ```
   Keep `~/.cloudflared/` out of git — it holds the tunnel
   credentials file.
5. In the Cloudflare dashboard, **Zero Trust → Networks → Tunnels**,
   open the tunnel and add a **Public Hostname**: your hostname →
   `http://localhost:8000`. This is the step that publishes the link.
6. Start the backend on port 8000 (it serves the UI and the API from
   one origin), then run the tunnel:
   ```bash
   cd services/agent-backend
   uvicorn main:app --host 127.0.0.1 --port 8000
   cloudflared tunnel run ai-kiosk
   ```
7. Verify: open the `https://` link in a browser, add
   `?mode=remote` to the Intercambio URL, upload a photo of a form,
   and check the agent answers. If the Jetson is off, the link is
   dead — that is expected, not a bug.

## Restrict testers later (optional)

In Zero Trust → Access, add an **Access application** on the same
hostname and allow only listed email addresses. No code change.

## What is never tunnelled

Ollama on `localhost:11434` — the model stays local-only. The tunnel
ingress has exactly one rule, to the backend on port 8000, plus a
catch-all 404.
