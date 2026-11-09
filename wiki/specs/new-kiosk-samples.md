# Spec — New kiosk samples: Shop Operator and Lifeboat

- **Issues:** [#35](https://github.com/23blocks-OS/ai-kiosk/issues/35) per-kiosk prompt and keys (part A), [#36](https://github.com/23blocks-OS/ai-kiosk/issues/36) Shop Operator (part B), [#37](https://github.com/23blocks-OS/ai-kiosk/issues/37) Lifeboat (part C).
- **Date:** 2026-11-09. **Status:** done (A and B). Part C is [raft-kiosk.md](raft-kiosk.md).
- **Approved by:** Juan, 2026-11-09: "approved."

## Goal
The launcher shows three working experiences: Nonprofit (Intercambio), Shop Operator and Raft. Each opens a kiosk page with its own prompt, its own service key and its own sample data. Each one works on the demo without a camera.

## Context
Decision 0001 left Shop and Lifeboat as "Coming soon". I deleted the three old placeholder pages (PR #33). `docs/architecture.md` says Shop sees a screenshot of the shop's Windows PC. `docs/lifeboat-eval.md` says Lifeboat answers from real manuals with citations. Aurelium has 8 GB and runs one 4B model, so the full Lifeboat library (55 to 210 GB, three extra model servers) does not fit. These are samples to demo the idea, not the products.

## Not in scope
- The full Lifeboat port (llama.cpp CUDA build, reranker, ZIM library). It stays in `docs/lifeboat-eval.md`.
- Embeddings or a vector database. Part C uses keyword scoring.
- Real shop software or real customer data. The shop is fictional.
- Voice for the new kiosks beyond what the shared shell already does.
- Medical, legal or dosage advice. The Lifeboat sample never states a dose.

## Approach
**A. One backend, one prompt per kiosk.** `/api/chat` and `/api/vision` accept a `kiosk` field (`intercambio` by default). A dict `PROMPTS` in `main.py` maps the name to a system prompt. An unknown name gets 400. The answer-language rule stays shared. Each page sends its own `kiosk` value and its own `app:<name>` key, the same way Intercambio does (decision 0008). No change to the key rules.

**B. Shop Operator.** A page at `apps/kiosk-shop/`, built from the Intercambio shell. It has three sample screenshots of a fictional "Ciao Shop" point-of-sale program (drawn as static images, no real software). The visitor taps a sample or uploads their own, types a task ("How do I print today's sales?") and the agent explains the steps it can see. It calls `/api/vision` with `kiosk=shop`. The prompt says: describe only what is visible, name the button or menu, say "I cannot see that on this screen" when it is missing, never guess a setting.

**C. Lifeboat.** *Superseded 2026-11-09 by [raft-kiosk.md](raft-kiosk.md), written after reading the Lifeboat repo. The text below is the first draft.* A page at `apps/kiosk-raft/`. A small library file `services/agent-backend/library/lifeboat-demo.json` holds about 12 short passages: title, text, source name, source URL, date fetched. Passages come only from US government public-domain pages (Ready.gov, FEMA, CDC, NWS). The backend scores passages by keyword overlap (lowercase, no stop words), takes the top 3 and puts them in the prompt. The prompt says: answer only from these passages; cite them as [1], [2]; if they do not cover the question, say "My sources do not cover this" and stop; never give a dose or a dilution; point to 911 for a life-threatening problem. The reply returns a `sources` list (title, source, URL) and the page shows it under the answer. No passage scores above zero means the backend skips the model and returns the honest "not covered" text at once. That also saves GPU time.

Alternatives dropped: one shared kiosk page with a mode switch (hides the three different jobs and breaks the per-app key rule); embeddings for retrieval (a new model on an 8 GB board for 12 passages).

## Where
- `services/agent-backend/main.py`: `PROMPTS`, `kiosk` field on `ChatRequest` and in `/api/vision`, `_retrieve(question)` and `/api/chat` `sources`.
- `services/agent-backend/library/lifeboat-demo.json` (new, committed; public-domain text only).
- `apps/kiosk-shop/{index.html,app.js,styles.css}` and `apps/kiosk-shop/samples/*.svg` (new).
- `apps/kiosk-raft/{index.html,app.js,styles.css}` (new).
- `apps/launcher/{index.html,app.js}`: Shop and Lifeboat cards become links; `?mode=remote` stays.
- `services/agent-backend/api-keys.example.json` and the real `api-keys.json` on Aurelium: add `app:shop`, `app:raft` (keys made on Aurelium, never printed).
- `services/agent-backend/README.md`, `README.md`, wiki pages, decision 0009.
- Tests: `tests/test_kiosks.py` (new).

## Steps
1. Juan approves this spec and answers the questions below.
2. `ciao-kiosk` writes the tests for A, they fail on today's code.
3. Part A: `PROMPTS`, `kiosk` field, tests pass. Merge, deploy.
4. Part B: Shop page and three sample screenshots. Tests, merge, deploy.
5. Part C: fetch about 12 passages from the named public-domain pages, show Juan the list with source URLs for review, then build retrieval and the page. Tests, merge, deploy.
6. `ciao-kiosk` makes the two keys on Aurelium, restarts, flips the launcher cards to links.
7. Live checks, wiki, decision 0009.

## Tests
- `test_unknown_kiosk_is_400`: `kiosk=nope` returns 400 and never calls the model. Fails today.
- `test_each_kiosk_gets_its_own_prompt`: the system message differs for `shop` and `lifeboat`. Fails today.
- `test_default_kiosk_is_intercambio`: no `kiosk` field keeps today's prompt. Passes today.
- `test_lifeboat_cites_sources`: a question about smoke finds the smoke passage; the reply has `sources`; the fake model sees only the top 3 passages.
- `test_lifeboat_not_covered_skips_the_model`: a question with no overlap returns "My sources do not cover this" and makes zero model calls.
- `test_lifeboat_library_is_public_domain_and_complete`: every passage has title, text, source, URL and date; every URL is on an allowed host list.
- `test_launcher_links_three_kiosks`: the launcher page links all three apps.
- `test_new_app_keys_are_app_scoped`: `app:shop` and `app:raft` keys get 403 on `/v1/*`.

## How we check it live
1. `https://kiosk.ciaocorp.com/apps/launcher/` shows three cards; each opens its page.
2. Shop: tap sample 1, ask "How do I print today's sales?", read an answer that names a visible button. Ask about something not on screen and read "I cannot see that".
3. Lifeboat: ask "What do I do about wildfire smoke?" and read an answer with [1] and a source link. Ask an unrelated question and read "My sources do not cover this" in under 2 seconds.
4. The log shows `route=chat user=app:lifeboat` and no question text.
5. `https://kiosk.ciaocorp.com/v1/models` is still 404.

## Deploy and rollback
Same as before: merge, `git pull` and `systemctl --user restart ai-kiosk` on Aurelium. Rollback: `git revert` the merge and restart. The two new keys stay in the key file and do no harm. Risk: low. Intercambio keeps its default prompt.

## Risks and open questions
- A 4B model can still mis-state a passage. The prompt limits it, the citation lets the visitor check, and the page says "Demo library. Not emergency advice. Call 911." Juan decides if that wording is enough.
- Ready.gov and CDC text is US government work and public domain, but I check each page's notice before I copy it.
- **Questions for Juan:** (1) Are Shop Operator and Lifeboat the "other samples"? (2) Lifeboat: is a 12-passage public-domain demo library right, or does he want a different source? (3) Shop: fictional Ciao Shop screens are fine? (4) Build order A, B, C is my recommendation.

## Result
A: PR #41, live. `kiosk` field with `PROMPTS`; unknown kiosk gives 400; an app key asking for another kiosk gives 403 (added beyond the spec). B: PR #44, live. Three fictional screens drawn by `apps/kiosk-shop/samples/make.py`. Live check: sample screen plus "How do I print the daily report?" named the Print Daily Report button in 8 s; "How do I issue a gift card?" answered "I cannot see that on this screen" (it then guessed "open the Settings tab", a weak spot). `kiosk-shop` is a copy of the Intercambio shell.
