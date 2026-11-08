# Spec 22 — Apps are service users: every model call carries an API key

- **Issue:** [#22](https://github.com/23blocks-OS/ai-kiosk/issues/22)
- **Date:** 2026-11-08. **Status:** draft, waits for Juan's approval.
- **Approved by:** not yet.

## Goal
Every route that reaches the model needs an API key. The kiosk apps are named service users, and the page sends its key. The logs show who called. A key can be revoked or rotated per app.

## Context
- **Juan, 2026-11-08:** "why the internal apps are not sending API keys, the api behavior should not change like that. add the apps (intercambio, etc) as service users with their keys and the app send keys to the api. does it make sense? that way the api endpoint works the same to all."
- Today `/v1/*` needs a key ([decision 0003](../decisions/0003-team-api-and-keys.md)). `/api/chat` and `/api/vision` need none, because the public page cannot keep a secret. Checked from outside on 2026-11-08: both answer without a key.
- **The limit that shapes the design:** the kiosk page is public (`kiosk.ciaocorp.com`). Any visitor can read the key the page holds. So an app key is an **identity tag**, not a secret.

## Not in scope
- A visitor login, or Cloudflare Access in front of the page (that would close the public demo).
- Request size limits ([#8](https://github.com/23blocks-OS/ai-kiosk/issues/8)) and GPU hogging ([#9](https://github.com/23blocks-OS/ai-kiosk/issues/9)). They stay open and still matter, because a scraped app key can still call `/api/*`.
- Moving the app from `/api/*` to `/v1/*`.

## Approach
1. **Service users in the same key file.** `api-keys.json` stays a flat `{"name": "key"}`. Apps are named `app:<kiosk>`, for example `app:intercambio`. The kiosk folder `kiosk-intercambio` maps to the user `app:intercambio`.
2. **Scope rule.** `_api_user` returns the name. `/api/*` accepts any valid key. `/v1/*` accepts a valid key whose name does **not** start with `app:`; an `app:` key gets 403 "this key is not allowed here".
   - **Why:** if an app key worked on `/v1`, any visitor could copy it from the page and use the team API. That would break the rule that `kiosk.ciaocorp.com` visitors see the app only.
3. **Check first.** `/api/chat` and `/api/vision` check the key before they read the body, the same order as `/v1` ([decision 0003](../decisions/0003-team-api-and-keys.md)). A missing or wrong key gets 401.
4. **The page gets its key from the server.** `GET /apps/<kiosk>/config.js` returns `window.KIOSK_CONFIG = {apiKey: "<key>"};` with `Cache-Control: no-store`. It is 404 if the app has no key. The key is never in git. The page loads `config.js` before `app.js`.
5. **The page sends it.** `apiPost` adds `Authorization: Bearer <key>`. On a 401 or 403 the page shows a plain message ("this app is not authorized"), not the "demo, not connected" text, because that would be false.
6. **Unchanged:** `/health` stays open. The selector page makes no model calls and needs no key.

**Other ways we considered:**
- Put the key in the page source in git: it leaks through the repo history.
- One shared person key in the page: it leaks a `/v1` key to every visitor.
- Hide a token in the backend only: that is the same as `/api/*` open, with extra steps.
- Put the page behind a login or Access: real secrecy, but the public demo closes.

## Where
- `services/agent-backend/main.py`: `_api_user` and a small scope check; key check at the top of `chat` and `vision`; a new route for `/apps/{kiosk}/config.js`, declared before the static mount.
- `apps/kiosk-intercambio/index.html`: one `<script src="config.js">` line before `app.js`.
- `apps/kiosk-intercambio/app.js`: `apiPost` header and the 401/403 message (plus ES/EN text).
- `services/agent-backend/api-keys.example.json`: add an `app:intercambio` line.
- `services/agent-backend/tests/`: new tests (below).
- `services/agent-backend/README.md`, `wiki/decisions/` (new decision 0008), `wiki/aurelium.md`.
- On Aurelium: add `app:intercambio` to `api-keys.json`.

## Steps
1. `ciao-kiosk`: branch, write tests first (they fail on today's code), then the code.
2. `ciao-kiosk`: run the tests and a browser check on a local server with a test key file.
3. `ciao-kiosk`: open the PR (links this spec and #22). Juan reviews and merges.
4. `ciao-kiosk`: on Aurelium, `git pull`; add `app:intercambio` with `openssl rand -hex 24`; restart the service. **Order matters:** add the key first, then restart. Without the key the page gets a 404 for `config.js` and cannot call the API.
5. `ciao-kiosk`: run the live checks below. Update the wiki and close #22.

## Tests
Each fails on today's code except where noted.
- `/api/chat` and `/api/vision` return 401 with no key and with a wrong key; no HTTP client toward Ollama is opened (same style as the `/v1` test).
- A valid person key works on `/api/chat`.
- An `app:intercambio` key works on `/api/chat` and gets 403 on `/v1/models` and `/v1/chat/completions`.
- `GET /apps/kiosk-intercambio/config.js` returns the key with `Cache-Control: no-store`; it returns 404 when the key file has no such app; it never appears in `GET /apps/kiosk-intercambio/` or in `app.js`.
- `/health` still needs no key. The static-file 404 tests still pass.

## How we check it live
Read back from outside, on `kiosk.ciaocorp.com`, `aureliano.twofourai.com` and the tailnet:
1. `POST /api/vision` with `{}` and no key: **401** (today: 400).
2. `GET /apps/kiosk-intercambio/config.js`: 200, `no-store`, contains a key.
3. That key on `/v1/models`: **403**. A person key on `/v1/models`: 200.
4. In a real browser, open the kiosk, ask one question, and get a model answer (the first call after idle can take about 2 minutes: [#10](https://github.com/23blocks-OS/ai-kiosk/issues/10)). The server log shows `user=app:intercambio`.
5. Remove the app key from the file: the page shows the "not authorized" message, not "demo". Put it back.

## Deploy and rollback
- **Deploy:** as in step 4. The key file is read on every request, so adding or removing a key needs no restart; the code needs one.
- **Rollback:** revert the PR and restart. The extra line in `api-keys.json` is harmless.
- **What can break:** a kiosk page cached in a browser from before the change keeps calling `/api/*` without a key and gets 401. A page reload fixes it. The idle reset reloads the kiosk every 3 minutes, so a real kiosk fixes itself.

## Risks and open questions
- **Not a secret.** Anyone can copy the app key from the page and call `/api/*`. It is the same exposure as today, now with a name in the logs. Abuse limits are #8 and #9.
- **Rotate:** to rotate an app key, edit the file. The page picks it up on the next load.
- **Open question for Juan:** should the `app:` keys also be limited to calls that come from the app's own hostnames (the `Origin` header)? It stops casual use from other websites, but a script can fake it. My default: no, keep it simple.

## Result
Not built yet.
