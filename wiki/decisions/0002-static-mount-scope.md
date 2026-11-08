# 0002 — Serve only apps/ and packages/shared-ui/

- **Date:** 2026-11-08. **Status:** accepted. **PR:** #1.
- **Context:** `main.py` mounted the whole repo root at `/`. Through the tunnel, `/.git/config`, the backend source and any `.env` answered 200. Reproduced with a test before the fix.
- **Decision:** Mount `/apps` and `/packages/shared-ui` only. Tests prove `.git`, `.env`, source and path-traversal URLs return 404.
- **Consequence:** `/` was a 404 until decision 0001 added the selector.
