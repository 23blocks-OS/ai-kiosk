# Spec — Raft kiosk (replaces part C of `new-kiosk-samples.md`)

- **Issue:** [#37](https://github.com/23blocks-OS/ai-kiosk/issues/37)
- **Date:** 2026-11-09. **Status:** draft. No code written.
- **Name:** Raft. Juan, 2026-11-09: "ok lifebote light it is , call it raft then". Raft is our small version of Lifeboat, built on the 4B model.
- **Approved by:** Juan approved the Lite approach and the name. The hero example and the starter shelf still wait for his word.
- **Source read:** `23blocks-OS/lifeboat`, fork of `johnpsasser/lifeboat`, HEAD `69b3ca1`, MIT. I read `README.md`, `DESIGN.md`, `app/{server,retrieve,llm,config,household}.py`, `sources.json`, `sources_pdf.json`, `regions/`, `scripts/{verify_offline,make_binder}.py` (2,601 lines in all).

## Goal
A visitor opens Raft on the kiosk, asks an emergency question, and gets a short cited answer from real public-domain manuals, or an honest "My sources don't cover this". The kiosk shows the source passage and proves the library is local.

## What Lifeboat is (from the code)
Lifeboat is a Mac-only emergency assistant. It has four parts.
1. **Library.** 76 PDFs (29 US-government public domain, 46 Hesperian "free for personal use", 1 local) plus Kiwix ZIM archives (medicine, water, repair, Wikipedia). About 55 GB, up to 210 GB with all of Wikipedia.
2. **Retrieval** (`retrieve.py`). SQLite FTS5 keyword search (BM25) and 1-bit vector search, plus live Wikipedia search. A reranker (bge-reranker-v2-m3) keeps the best 8 passages, at most 2 per page. An `EXPAND` table turns everyday words into manual words ("heart attack" adds "myocardial infarction").
3. **Answer** (`server.py`). A 12-rule system prompt: cite every claim `[n]`, say "My sources don't cover this", never invent a dose, lead with numbered steps, name danger signs. Three llama-server processes (chat, embedding, reranker). The chat model is 27B to 35B.
4. **Guards and extras.** A child-dose check in code, on the finished answer. Household intake (ages, medicines, allergies). A region file. `verify-offline` (proves no network use). `make_binder` (prints about 50 procedures as verbatim source text, no AI words).

## What does not carry to Aurelium
- The three-server design needs about 25 GB of memory. Aurelium has 8 GB, and the Qwen3-VL 4B model already uses almost all of it (80 MB free).
- The installer refuses anything but Apple Silicon. A Jetson port is real work (`docs/lifeboat-eval.md`).
- Household intake stores health data. The kiosk is public and "nothing is recorded".
- Hesperian PDFs allow personal, non-commercial use only. Wikipedia and Stack Exchange need CC BY-SA credit. A public kiosk demo uses neither.

## What we reuse (MIT, keep the license notice)
The **ideas and short pieces of code**, not the platform: the system prompt rules, the `EXPAND` table, the `STOP` word list, `_fts_query`, `extract.chunk` (1,400 characters, 150 overlap), and the child-dose guard `_dose_warning`. These run in our FastAPI backend with Python's built-in `sqlite3` (FTS5) and `pypdf`. The model stays our `qwen3-vl:4b-instruct` through Ollama.

## Which example is the most interesting
Ranked for a live demo on this kiosk.
1. **Wildfire smoke in Boulder County.** The Marshall fire (December 2021) is local memory. Sources exist in the public-domain set: `ready-wildfire-info-sheet`, `epa-wildfire-smoke-guide`. The question "Wildfire smoke is heavy outside. How do I protect my family indoors?" is in Lifeboat's own test list. **Recommended hero.**
2. **The child-dose guard.** Ask "My 4-year-old has a fever. How much ibuprofen?" The answer carries a red box written by code, not by the model. It shows why a small local model needs a guard. **Recommended safety moment.**
3. **"My sources don't cover this."** Ask something off the shelf. The kiosk refuses to guess. Cheap and convincing.
4. **Power outage and generator safety** (`ready-power-outage-info-sheet`, `cdc-generator-co-safety`, `cpsc-generator-safety`). Carbon monoxide is the classic outage death.
5. **Offline proof.** A badge "Library on this box: 10 documents, 0 network calls while answering". It matches `verify-offline`.
6. **Paper binder.** A print button that gives the verbatim passage, no AI text. Needs a printer; later.

## Not in scope
Household intake; embeddings and reranker; Wikipedia, Stack Exchange and Hesperian content; offline maps; the full Jetson port; voice beyond the shared shell. Phase 2 below covers vectors.

## Approach
**Phase 1, Raft (this spec).** A starter shelf of ten US-government PDFs (about 60 MB), indexed once into one SQLite FTS5 file. At question time: expand the question, take the top 3 passages by BM25 (two per page at most), cut each to 1,200 characters, build the prompt with Lifeboat's rules, call Ollama, run the dose guard, return `answer`, `sources` and an optional `warn`. If BM25 returns nothing, skip the model and return the "not covered" text.

**Starter shelf** (ids from `sources_pdf.json`; Juan reviews before ingest): `ready-wildfire-info-sheet`, `epa-wildfire-smoke-guide`, `ready-power-outage-info-sheet`, `cdc-generator-co-safety`, `cpsc-generator-safety`, `cdc-make-water-safe`, `fema-food-water-emergency`, `tc-4-02-1-first-aid`, `niosh-poisonous-plants`, `fema-are-you-ready`. I check each license line when I download it.

**Why not run Lifeboat itself.** Raft is the small version. Memory. The 4B model plus embedding and reranker servers do not fit in 8 GB.

**Phase 2 (later, only if Phase 1 answers miss).** Add vectors with a small Ollama embedding model, measure memory first. Not started.

**Latency.** Lifeboat sends 8 passages of up to 3,500 characters (about 7,000 tokens). Our Ollama context is 4,096 tokens. Three passages of 1,200 characters (about 1,000 tokens) fit. I measure the full answer time on Aurelium before I claim a number. The Cloudflare limit is about 100 s and our timeout is 90 s.

## Where
- `services/agent-backend/raft/` (new package): `library.py` (ingest, `sqlite3` FTS5), `retrieve.py` (`expand`, `search`), `guard.py` (`dose_warning`), `prompt.py` (rules).
- `services/agent-backend/raft/shelf.json`: ten entries (id, title, URL, license, date fetched, sha256). PDFs and the index file `raft.sqlite` are gitignored. `scripts/build_shelf.py` downloads, checks sha256, extracts and indexes.
- `services/agent-backend/main.py`: `/api/chat` with `kiosk=raft` calls the package and returns `sources` and `warn`. Depends on #35.
- `apps/kiosk-raft/{index.html,app.js,styles.css}`: chat, a sources panel with the passage text, the red warning box, the badge, the 911 line.
- A `NOTICE` file with the MIT text of the upstream project.
- `services/agent-backend/requirements.txt`: `pypdf` (pinned).
- Tests: `tests/test_raft.py`.

## Steps
1. Juan approves this spec and picks the hero example.
2. `ciao-kiosk` builds #35 first (the `kiosk` field and keys).
3. `ciao-kiosk` downloads the ten PDFs on Aurelium and shows Juan the table: id, URL, license line, pages, passages indexed.
4. Juan confirms the shelf.
5. Tests first (they fail), then the package and the endpoint.
6. The page. The launcher card becomes a link.
7. Live checks, wiki, decision 0009.

## Tests
- `test_expand_adds_manual_words`: "heart attack" adds "myocardial infarction".
- `test_demo_questions_find_their_passage`: five demo questions (wildfire smoke, generator, boil water, deep cut, poison ivy) each return a passage from the expected document in the top 3. Lifeboat's roadmap lists this field-test suite as missing.
- `test_not_covered_skips_the_model`: "How do I file taxes?" returns the honest text and makes zero model calls.
- `test_prompt_carries_the_rules`: the system message holds the citation rule, the no-invented-dose rule and the 911 line.
- `test_child_dose_guard`: a child question plus an answer with "400 mg" gives a warning; an adult question gives none; an answer with an adult daily maximum for a child adds the stronger text.
- `test_sources_are_returned_and_cited`: the reply lists up to 3 sources with title, document and page.
- `test_shelf_is_public_domain`: every `shelf.json` entry has a license that starts with "US Gov public domain" and an allowed host.
- `test_raft_key_is_app_scoped`: `app:raft` gets 403 on `/v1/*`.
- `test_log_has_no_question`: the call log line names `kiosk=raft` and holds no question text.

## How we check it live
1. `https://kiosk.ciaocorp.com/apps/launcher/` opens Raft.
2. Wildfire smoke question: answer with `[1]` and a source panel, time recorded.
3. Child ibuprofen question: the red box shows.
4. A tax question: "My sources don't cover this" in under 2 seconds.
5. `ollama ps` shows one model. Free memory is not lower than today.
6. The log shows `route=chat user=app:raft` and no question text. `/v1/models` on `kiosk.ciaocorp.com` is still 404.

## Deploy and rollback
`git pull`, run `scripts/build_shelf.py` once, restart the service. Rollback: `git revert` the merge and restart. The shelf files stay on disk. Intercambio does not change.

## Risks and open questions
- **Safety.** A 4B model can misread a passage. Mitigation: three short passages, citation rules, the code guard, a visible source panel, and the line "Demo library. Not emergency advice. In an emergency, call 911." on every answer. Juan decides the wording.
- **Accuracy claim.** I do not claim any accuracy number until the five-question suite and the live checks are done.
- **Latency.** Unknown until measured on Aurelium.
- **Boulder-specific sources.** I have not found or checked a Boulder County document. Juan can point me to one; otherwise the shelf stays national.
- **Questions for Juan:** (1) Is the hero "wildfire smoke" plus the child-dose guard? (2) Is the ten-PDF starter shelf right? (3) Answered: Raft on our 4B model, the full port later.

## Result
Filled after the work.
