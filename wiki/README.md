# AI Kiosk wiki

The project's memory. Plain markdown, kept by `ciao-kiosk` (an AI agent), read by everyone.
It follows Karpathy's "LLM wiki" pattern: the agent writes the pages, so knowledge adds up instead of being re-derived every session.

## Three layers

| Layer | Where | Rule |
| --- | --- | --- |
| Sources | `sources/` | Raw material (handoffs, messages, notes). Never edited after it is added. |
| Pages | everything else | The agent writes and updates them. Each fact lives in one page; other pages link to it. |
| Schema | this file | How the wiki works. Change it only on purpose, and log the change. |

## Files

- `index.md` — catalog of every page, one line each. Read it first.
- `log.md` — append-only history. One dated line per event. Never rewrite old lines.
- `backlog.md` — what to do next, by priority. Each audit finding has a row, a GitHub issue and, later, a spec.
- `specs/` — one detailed spec per item we decide to work on. Template: [specs/TEMPLATE.md](specs/TEMPLATE.md).
- `decisions/NNNN-title.md` — one decision per page: context, decision, why, consequences.
- `aurelium.md` — the Jetson: facts, how it runs, runbook.
- `sources/` — raw inputs, named `YYYY-MM-DD-who-topic.md`.

## From finding to done

1. **Finding.** Write a GitHub issue (what is wrong, evidence, proposed fix, what happens if we skip it) and a row in `backlog.md` with the issue link.
2. **Decision.** Juan says which item we work on.
3. **Spec.** `ciao-kiosk` writes `specs/issue-<N>-title.md` from the template: goal, approach, exact files, steps, tests, live checks, deploy and rollback. Juan reads it and approves it. No code before this.
4. **Build.** Branch, code, tests, PR. The PR links the issue and the spec.
5. **Done.** Merge, deploy, check from outside, fill the spec's Result section, move the row to Done, add a line to `log.md`, close the issue.

## Operations

- **Ingest.** New source or news: save the source, update the pages it changes, add it to `index.md`, add a line to `log.md`.
- **Query.** Read `index.md`, open the pages it points to, answer. If the answer is worth keeping, write it into a page.
- **Lint.** Now and then: find dead links, pages missing from the index, stale facts, backlog items already done, and decisions that contradict each other. Fix them and log it.

## Rules

1. **Decide, then record.** When Juan decides, write a `decisions/` page the same day. Quote his words.
2. **Date everything** (`2026-11-08`). Mark a replaced decision `superseded by NNNN`; never delete it.
3. **Link, do not copy.** Use relative links.
4. **No secrets.** No keys, tokens or passwords. Say where a secret lives, never what it is.
5. **Say what is verified.** Write "checked on 2026-11-08 from outside" or "not checked".
6. **Writing style:** short sentences, active voice, one word one meaning.
