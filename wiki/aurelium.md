# Aurelium (the Jetson)

Facts from the Lares handoff ([source](sources/2026-11-08-lares-handoff.md)) and from `ciao-kiosk` checks on 2026-11-08.

## Device
- NVIDIA Jetson Orin Nano Super, hostname `aurelian`. 8 GB shared memory, 1 TB NVMe. Ubuntu 24.04, Jetson Linux R39.2.1.
- LAN `10.0.0.94`. Tailscale `100.104.207.74`, name `aurelian.rhinoceros-centauri.ts.net`. User `jpelaez`. `sudo` needs Juan's password.
- Memory is tight: about 80 MB free with a model loaded (checked 2026-11-08).
- Ollama on `127.0.0.1:11434`, never exposed. Models: `qwen3-vl:4b`, `qwen3-vl:4b-instruct`.

## How the app runs
- Code: `~/ai-kiosk` (clone of `23blocks-OS/ai-kiosk`). Update with `git pull`.
- Backend: user service `ai-kiosk`, port 8000, all interfaces, `--no-proxy-headers`, env `APP_ONLY_HOSTS=kiosk.ciaocorp.com`. Venv at `~/ai-kiosk/.venv`.
- Keys: `~/ai-kiosk/services/agent-backend/api-keys.json`. Gitignored. See [decision 0003](decisions/0003-team-api-and-keys.md).
- Tunnel: Cloudflare Tunnel `cloudflared` (system service, managed in the Cloudflare dashboard) sends both hostnames to `localhost:8000`.

## URLs
| URL | App | API |
| --- | --- | --- |
| `https://kiosk.ciaocorp.com` | yes | no |
| `https://aureliano.twofourai.com` | yes | yes, with key |
| tailnet `:8000` | yes | yes, with key |

## Runbook
- Status: `systemctl --user status ai-kiosk`. Logs: `journalctl --user -u ai-kiosk -f`.
- Restart: `systemctl --user restart ai-kiosk`.
- Deploy: `cd ~/ai-kiosk && git pull && systemctl --user restart ai-kiosk`.
- Access from the Mac Mini: `ssh aurelium` (dedicated key `~/.ssh/ciao-kiosk_aurelium`).
- Check from outside: `/health` returns 200; `/.git/config` returns 404; `/v1/models` returns 401 without a key.
