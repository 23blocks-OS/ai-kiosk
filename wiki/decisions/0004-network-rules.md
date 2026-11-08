# 0004 — Who sees what

- **Date:** 2026-11-08. **Status:** accepted. **PR:** #4 (open).
- **Juan's rule:** tailnet users see the app and the API. People on `twofourai.com` see the app and the API. People on `ciaocorp.com` see only the app.

| Where the caller comes from | App | API (`/v1`) |
| --- | --- | --- |
| Tailnet | yes | yes, with key |
| `aureliano.twofourai.com` | yes | yes, with key |
| `kiosk.ciaocorp.com` | yes | no |

- **How:** env `APP_ONLY_HOSTS=kiosk.ciaocorp.com` makes `/v1/*` a 404 on that host, even with a valid key. The backend checks the `Host` header, which Cloudflare sets.
- **Rejected:** Tailscale identity headers for trust. The tunnel passes client headers through, so anyone could forge them.
- **Rejected:** two backend processes (one per network). Each has its own GPU limit, so the Jetson could take 4 calls and run out of memory.
- **Status check:** until PR #4 is merged and deployed, `kiosk.ciaocorp.com` still reaches `/v1` (key required).
