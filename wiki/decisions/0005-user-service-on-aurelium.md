# 0005 — Backend runs as a user service on Aurelium

- **Date:** 2026-11-08. **Status:** accepted, with one open step.
- **Context:** `ciao-kiosk` has no sudo on Aurelium. Juan types the password.
- **Decision:** `systemd --user` service `ai-kiosk`, uvicorn on `0.0.0.0:8000` with `--no-proxy-headers`.
- **Why all interfaces:** `/v1` needs a key everywhere and the kiosk routes are public through the tunnel anyway, so the LAN gains almost nothing. Tailscale Serve would keep the backend on localhost, but it needs sudo once.
- **Why `--no-proxy-headers`:** it stops a caller from faking `X-Forwarded-For`.
- **Open step:** the service stops at reboot until Juan runs `sudo loginctl enable-linger jpelaez`. See [backlog](../backlog.md) item 1.
