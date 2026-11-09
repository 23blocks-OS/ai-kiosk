# Log

Append only. Newest at the bottom.

- 2026-11-08 — `ciao-kiosk` receives the handoff from Lares (IT). Saved as a source.
- 2026-11-08 — Found that the backend served the whole repo, `.git` included, through the tunnel. Fixed in PR #1. See decision 0002.
- 2026-11-08 — Kiosk selector added at `/` (PR #2). Decision 0001.
- 2026-11-08 — Backend deployed on Aurelium. Both public URLs checked from outside.
- 2026-11-08 — Team API `/v1` added with API keys (PR #3). Decision 0003.
- 2026-11-08 — Juan sets the network rules. `kiosk.ciaocorp.com` gets the app only (PR #4, open). Decision 0004.
- 2026-11-08 — Wiki created.
- 2026-11-08 — Juan: the key must be validated before any call reaches Ollama. Already true for `/v1`; test added to PR #4. Open point: the kiosk page's own `/api/chat` and `/api/vision` have no key (see backlog 13).
- 2026-11-08 — PRs #4, #5, #6 merged and deployed to Aurelium. Network rule checked from outside: `kiosk.ciaocorp.com` app only; `aureliano.twofourai.com` and the tailnet app + API.
- 2026-11-08 — Home button and idle reset live (decision 0006). Record repo pushed to `3Metas/ciao-kiosk`.
- 2026-11-08 — A test called the real model on Aurelium and timed out. Fixed: tests never call the real model.
