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
- 2026-11-08 — Ponytail audit of the repo: 13 findings. Opened GitHub issues #8 to #20, one per finding, and a backlog row for each. Added the spec template and the finding-to-done workflow.
- 2026-11-08 — Juan decides the kiosk apps must send API keys as named service users. Issue #22 and spec 22 written (draft). Key point: a key in a public page is an identity tag, not a secret, so `app:` keys work on `/api/*` only.
- 2026-11-08 — Juan reports the kiosk shows STUB. Cause: reasoning model too slow, backend timeout at 120 s. Fixed on Aurelium by switching to `qwen3-vl:4b-instruct` (decision 0007, issue #23). False stub text on timeout is issue #24.
- 2026-11-08 — Spec 22 built, merged (PR #25) and deployed. Live checks passed on all three paths; real visitor flow answered in about 20 s as `app:intercambio`. Decision 0008.
- 2026-11-08 — Juan asks about logs. Found: errors swallowed, no duration or outcome, every visitor shows as 127.0.0.1. Issue #28. Also: issue #26 (stale page, false demo text) fixed in PR #27, not yet merged.
- 2026-11-09 — Hardening (PR #30) and `no-store` (PR #29) merged and deployed; wiki PRs #7, #21 merged. Read-backs passed through Cloudflare.
- 2026-11-09 — Juan: English question got a Spanish answer. Cause: the prompt said "Spanish is the default" and ignored the UI language. Fixed in PR #31: answer in the visitor's language; UI language is the fallback.
- 2026-11-09 — Juan asks for the other kiosk samples. Issues #35 #36 #37 and spec `new-kiosk-samples.md` written (draft). Also: favicon (PR #34), double-send block, vision tests, placeholder pages deleted (PR #33).
- 2026-11-09 — Juan: read the Lifeboat repo, spec only. Read all 2,601 lines. Finding: reuse prompt, retrieval ideas and the child-dose guard in our backend on the 4B model; the full port does not fit 8 GB. Spec `lifeboat-kiosk.md` (draft).
