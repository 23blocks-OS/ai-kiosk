# Spec — Raft shelf loader (load and unload library packs by situation)

- **Issue:** [#42](https://github.com/23blocks-OS/ai-kiosk/issues/42). **Depends on:** [#37](https://github.com/23blocks-OS/ai-kiosk/issues/37) (Raft).
- **Date:** 2026-11-09. **Status:** draft. No code written. Build after Raft Phase 1.
- **Approved by:** waits for Juan.
- **Juan's words, 2026-11-09:** "as the memory is limited, can we create a loader than upload , remove from memory the elements we need? because storage is cheap, so we can decide, lets start loading this elements to memory based on the emergency or situation. does it make sense?"

## Goal
Raft keeps many library packs on disk and holds only the packs for the current situation in memory. An operator, or a visitor's question, brings the right pack in and pushes the unused ones out. The kiosk shows which situation is loaded.

## Does it make sense? Yes, with one correction.
The idea is right. The numbers matter.
- **Packs are small.** The ten-PDF starter shelf is about 60 MB of PDFs and an estimated 20 to 40 MB of search index. I have not measured it. Memory is not the limit for that size.
- **The model is the memory problem.** `qwen3-vl:4b-instruct` takes 4.0 GB. Aurelium has 80 MB free with it loaded.
- **Storage is cheap.** The board has a 1 TB NVMe. A shelf of 20 to 50 GB of packs fits on disk. Then the packs are too big to hold all at once, and the loader earns its place.
- **So the loader has two jobs.** Job 1 (this spec): keep big packs on disk and load only the active ones into memory. Job 2 (later, optional): load a larger helper model, for example an embedding model for meaning search, only while a situation needs it. Job 2 needs a measured memory budget first.

## Not in scope
Swapping the chat model per situation (Phase 3, only if measured). Downloading packs at run time (the kiosk makes no outside calls while answering; packs are built ahead with `scripts/build_shelf.py`). Automatic alerts from outside (needs internet; an operator sets the situation).

## Approach
**Packs.** One pack is one SQLite FTS5 file plus a `manifest.json`: name, situation tags, a keyword list, source documents (id, license, sha256), size on disk, estimated size in memory. Examples: `first-aid` (always on), `wildfire`, `power-outage`, `water`, `earthquake`, `winter-storm`, `plants`. Packs live in `services/agent-backend/raft/packs/` (gitignored, built by script).

**Loader.** A small module `raft/loader.py` with a memory budget in MB (env `RAFT_MEMORY_MB`, default 200).
- `load(pack)`: copy the pack's SQLite file into an in-memory database (SQLite backup API). Add its size to the used total. If the total goes over the budget, unload the least recently used pack that is not pinned.
- `unload(pack)`: close the in-memory database.
- `status()`: the loaded packs, size of each, budget, free budget.
- Pinned packs (`first-aid`) never unload.
- A pack that cannot fit alone gets a clear error, not a crash.

**Which pack answers.** Search runs over the loaded packs only. A tiny always-loaded index of pack names and keywords (a few KB) lets Raft see when a question belongs to an unloaded pack. Then Raft loads that pack from disk (a copy of tens of MB takes well under a second) and answers. The reply says which shelf it used. If no pack matches, the honest "My sources don't cover this" returns.

**Situation.** An operator sets the situation (for example "wildfire") with a person key. The loader pre-loads the matching packs. This is the demo moment: the operator taps "Wildfire", the page banner changes, the right shelf is warm. App keys cannot set the situation (403), so a visitor cannot change it.

**Why this way.** Loading on demand alone is simple but hides the idea. Setting a situation alone fails when a visitor asks about something else. Both together give a story and a safety net. Dropped: keeping everything in one big index (grows without limit, no control over memory); a separate process per pack (one more process on an 8 GB board).

## Where
- `services/agent-backend/raft/loader.py` (new), `raft/packs.py` (manifest reader, pack router).
- `services/agent-backend/raft/packs/*.sqlite` and `*.json` (gitignored). `scripts/build_shelf.py` gains `--pack <name>`.
- `main.py`: `GET /api/raft/shelf` (status, any key), `POST /api/raft/situation` (person key only), and a `shelf` field in the Raft reply.
- `apps/kiosk-raft/`: a situation banner, and a small operator panel (hidden unless `?operator=1`; the call still needs a person key).
- Env: `RAFT_MEMORY_MB`. Docs: README, wiki.
- Tests: `tests/test_raft_loader.py`.

## Steps
1. Juan approves this spec. Raft Phase 1 (#37) is merged first.
2. Measure: the real index size of the starter shelf, and free memory on Aurelium with Raft running. Write the numbers into this spec.
3. Tests first (they fail).
4. Split the starter shelf into packs. Build the loader and the router.
5. Add the endpoints, the banner and the operator panel.
6. Live checks, wiki, decision.

## Tests
- `test_load_and_unload_change_the_used_memory`: loading a pack raises the used total by its size; unloading lowers it.
- `test_over_budget_unloads_the_least_recently_used`: with a small budget, loading a third pack drops the oldest unpinned pack.
- `test_pinned_pack_never_unloads`: `first-aid` stays through every eviction.
- `test_a_pack_larger_than_the_budget_is_refused_cleanly`: a clear error, nothing else unloads.
- `test_question_for_an_unloaded_pack_loads_it`: a power-outage question loads `power-outage` and the reply names the shelf.
- `test_unmatched_question_is_not_covered`: no pack matches, no model call.
- `test_app_key_cannot_set_the_situation`: 403. A person key gets 200 and the packs load.
- `test_status_lists_loaded_packs_and_budget`.
- `test_log_has_no_question`: the loader logs pack names and sizes, never the question.

## How we check it live
1. `GET /api/raft/shelf` with a person key lists `first-aid` loaded and the budget.
2. Set situation "wildfire". The banner changes. A wildfire smoke question answers with a wildfire source.
3. Ask a power-outage question. The reply names the `power-outage` shelf. `status` shows the swap.
4. `free -m` and `ollama ps` on Aurelium: free memory is not lower than before Raft, and the model is still loaded.
5. A visitor key on `POST /api/raft/situation` returns 403.

## Deploy and rollback
`git pull`, build the packs once, restart. Rollback: `git revert` the merge and restart. The single-index Raft from Phase 1 still works without the loader.

## Risks and open questions
- Memory is tight. The default budget of 200 MB is a guess until step 2 measures. If the model gets memory-pressured, the budget goes down.
- A wrong situation set by an operator hides useful packs. The on-demand load is the safety net.
- **Questions for Juan:** (1) Is an operator-set situation plus on-demand loading right? (2) Which situations first: wildfire, power outage, water, first aid? (3) Is the always-on pack just `first-aid`?

## Result
Filled after the work.
