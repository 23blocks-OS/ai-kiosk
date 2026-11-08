# Source: Lares handoff, 2026-11-08

Raw summary of the AMP message from `systemai` (Lares, IT support), msg `msg_1794169500466_jcfdozk`. Not edited after saving.

- Aurelium device facts: see [aurelium.md](../aurelium.md).
- Cloudflare Tunnel `8e3628ed-e151-4f51-9776-cf0a7c345311`, remote-managed, hostnames `aureliano.twofourai.com` and `kiosk.ciaocorp.com`, both to `http://localhost:8000`. Both gave 502 before the backend ran.
- Juan wants both URLs to serve the app and the API. The API must also work on its own.
- Open items Lares listed: venv missing; `StaticFiles` mounted the repo root (would publish `/.git/`); API has no auth; internal use without Cloudflare; CORS; run at boot.
- Lares can add `ciao-kiosk`'s SSH key and help with network and sudo steps: `systemai@rnd23blocks.aimaestro.local`.
