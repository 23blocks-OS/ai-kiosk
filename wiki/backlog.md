# Backlog

Priority order. Move done items to the bottom with the date. `Juan` means it needs his sudo or his decision.

## Now
1. **Reboot survival.** Juan runs `sudo loginctl enable-linger jpelaez` on Aurelium. Without it, the backend stops at reboot.

## Next
2. **Cold start.** The first call after idle took about 2 minutes. Keep the model loaded (`OLLAMA_KEEP_ALIVE`; needs Juan's sudo).
3. **Upload size cap** on `/api/vision`. Today it has none.
4. **Fix the stale cloudflared docs.** The tunnel is managed in the Cloudflare dashboard and runs as a service. The docs describe a local config and `/home/jetson`.
5. **Per-kiosk prompt.** `/api/chat` has one Intercambio prompt. Add a `kiosk` field when a second kiosk needs different behavior.
6. **Streaming for `/v1`.** Not supported now. Many OpenAI clients stream.

## Later
7. Remove the unlinked `apps/kiosk-nonprofit/` stub.
8. Fix the broken link `apps/website/index.html` to `../docs/architecture.md`.
9. Whisper and Piper (voice) are not installed on Aurelium.
10. CORS, only if browser apps on other sites will call the API.
11. Cloudflare Access on `aureliano.twofourai.com`. Optional now that keys exist.
12. PR #1 commit is authored as "Juan Pelaez", not `ciao-kiosk`. Rewrite only if Juan asks.
13. **Kiosk page API has no key.** `/api/chat` and `/api/vision` reach Ollama without a key, because the public page cannot hold a secret. Anyone can call them with curl. Options: leave it (demo, 2-call limit), a rate limit per IP, or Cloudflare Access on `aureliano.twofourai.com` only. Needs Juan's decision.

## Done
- 2026-11-08 — Repo-root leak closed (PR #1). Selector (PR #2). Team API with keys (PR #3). Backend live on Aurelium.
- 2026-11-08 — `kiosk.ciaocorp.com` gets the app only (PR #4). Checked from outside: `/v1` is 404 there, even with a key.
- 2026-11-08 — Home button and idle reset (PR #6). Wiki (PR #5).
- 2026-11-08 — Record repo pushed to `3Metas/ciao-kiosk`.
