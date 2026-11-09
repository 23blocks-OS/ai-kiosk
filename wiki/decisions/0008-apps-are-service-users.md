# 0008 — Apps are service users with API keys

- **Date:** 2026-11-08. **Status:** accepted, live. **Issue:** [#22](https://github.com/23blocks-OS/ai-kiosk/issues/22). **PR:** #25. **Spec:** [issue-22](../specs/issue-22-apps-as-service-users.md).
- **Juan's words:** "why the internal apps are not sending API keys, the api behavior should not change like that. add the apps (intercambio, etc) as service users with their keys and the app send keys to the api."
- **Decision:** every route that reaches the model needs a key, including `/api/chat` and `/api/vision`. Apps are service users named `app:<kiosk>` in `api-keys.json`. The server gives each page its key at `/apps/<kiosk>/config.js`. A page sends it as a Bearer token.
- **Scope rule:** an `app:` key works on `/api/*` and gets 403 on `/v1/*`.
- **Why the scope rule:** the kiosk page is public. Any visitor can read its key. An app key is an identity tag (named logs, revoke, rotate), not a secret. If it worked on `/v1`, every visitor would get the team API.
- **What it does not do:** it does not stop abuse of `/api/*`. Anyone can copy the key. See issues #8 and #9.
- **Rejected:** a key in the page source in git (leaks in history); one shared person key in the page (leaks `/v1`); a hidden backend-only token (same as an open route); a login or Cloudflare Access in front of the page (closes the public demo).
- **To add a kiosk:** `openssl rand -hex 24`, add `"app:<name>": "<key>"`, load `config.js` before `app.js`.
