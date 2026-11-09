# 0001 — Kiosk selector is the front page

- **Date:** 2026-11-08. **Status:** accepted. **PR:** #2.
- **Context:** Juan wants to demo the AI Kiosk itself. The app must open on a choice of experiences (Nonprofit, Shop, and so on). Only one is built.
- **Decision:** `/` redirects to `/apps/launcher/`. One card per kiosk. "Nonprofit" opens Intercambio. Shop and Lifeboat show "Coming soon" and are not links.
- **Juan's words:** "Intercambio is non profit demo."
- **Why:** The demo never lands on an empty page. The old `apps/kiosk-nonprofit/` stub is unlinked (backlog 7).
- **Consequence:** `?mode=remote` passes through the redirect and onto the card link.
