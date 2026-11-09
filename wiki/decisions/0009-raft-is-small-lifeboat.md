# 0009 — Raft is a small Lifeboat on our own model

- **Date:** 2026-11-09. **Status:** accepted. **Issue:** #37. **Spec:** [raft-kiosk.md](../specs/raft-kiosk.md).
- **Context:** The Lifeboat repo needs about 25 GB of memory, three model servers and Apple Silicon. Aurelium has 8 GB and the 4B model fills it.
- **Decision:** Build "Lifeboat Lite", named **Raft**. It reuses Lifeboat's prompt rules, word table and child-dose guard, with keyword search over ten public-domain PDFs, on `qwen3-vl:4b-instruct`. The full port stays a later option.
- **Juan's words:** "ok lifebote light it is , call it raft then"
- **Why:** It fits the board, keeps citations and the code guard, and demos the idea now.
- **Consequence:** Kiosk name `raft`, key `app:raft`, folder `apps/kiosk-raft/`. The launcher card is "Raft".
