# Backlog

Priority order. Every audit finding has a GitHub issue and a row here. When we decide to work on an item, `ciao-kiosk` writes a spec in `specs/` first ([template](specs/TEMPLATE.md)), then builds. Move finished items to Done with the date.

## Needs Juan (sudo or a decision)
- **Reboot survival.** Run `sudo loginctl enable-linger jpelaez` on Aurelium. Without it, the backend stops at reboot.
- **Keep the model loaded for `/v1`.** `OLLAMA_KEEP_ALIVE` on the Ollama service needs sudo. Part of [#10](https://github.com/23blocks-OS/ai-kiosk/issues/10).
- **Who stops a visitor from holding the GPU?** Cloudflare rate-limit rule (no code) or a backend limit. Decides [#9](https://github.com/23blocks-OS/ai-kiosk/issues/9).
- **PR #1 author.** The commit says "Juan Pelaez", not `ciao-kiosk`. Rewrite only if Juan asks.

## Planned (spec drafted, waits for Juan's approval)
- [#35](https://github.com/23blocks-OS/ai-kiosk/issues/35) Per-kiosk prompt and keys, [#36](https://github.com/23blocks-OS/ai-kiosk/issues/36) Shop Operator sample, [#37](https://github.com/23blocks-OS/ai-kiosk/issues/37) Raft sample (small Lifeboat). [Spec](specs/new-kiosk-samples.md); Raft (the Lifeboat sample) has its own [spec](specs/raft-kiosk.md) after reading the repo. Juan, 2026-11-09: "lets now build the other samples we have plan, write the backlog item, and the spec first."

- [#42](https://github.com/23blocks-OS/ai-kiosk/issues/42) Raft shelf loader: load and unload library packs by situation. [Spec](specs/raft-shelf-loader.md). Comes after Raft Phase 1. Juan, 2026-11-09: "load this elements to memory based on the emergency or situation."

## In progress
- ~~**Hardening** — #8, #10, #11, #24, #28 (part of #12).~~ Done 2026-11-09, PR #30. [Spec](specs/hardening-8-10-11-24-28.md). Juan: "go go, go, we are way behind on this."

## Audit findings (ponytail audit, 2026-11-08)

Finding numbers are from the audit report. Issue numbers are GitHub's.

| # | Issue | Level | What | Spec | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | [#8](https://github.com/23blocks-OS/ai-kiosk/issues/8) | must-fix | Public routes accept unlimited request size (out-of-memory risk) | — | done 2026-11-09 |
| 2 | [#9](https://github.com/23blocks-OS/ai-kiosk/issues/9) | must-fix | Any visitor can hold the GPU and block everyone, team API included | — | open, needs Juan |
| 3 | [#10](https://github.com/23blocks-OS/ai-kiosk/issues/10) | must-fix | First request after idle fails (cold start longer than Cloudflare's limit) | — | done 2026-11-09 |
| 4 | [#11](https://github.com/23blocks-OS/ai-kiosk/issues/11) | should-fix | `/v1` returns 500 on a JSON list body or a bad key file | — | done 2026-11-09 |
| 5 | [#12](https://github.com/23blocks-OS/ai-kiosk/issues/12) | should-fix | No tests for the honest fallback, the queue 503 and `/api/vision` | — | open |
| 6 | [#13](https://github.com/23blocks-OS/ai-kiosk/issues/13) | should-fix | Kiosk lets a visitor send many messages while the agent is thinking | — | open |
| 7 | [#14](https://github.com/23blocks-OS/ai-kiosk/issues/14) | should-fix | Pin Python package versions, add dev requirements | — | open |
| 8 | [#15](https://github.com/23blocks-OS/ai-kiosk/issues/15) | should-fix | Setup docs describe a setup that is not running | — | open |
| 9 | [#16](https://github.com/23blocks-OS/ai-kiosk/issues/16) | should-fix | Delete three unlinked placeholder kiosk pages | — | open |
| 10 | [#17](https://github.com/23blocks-OS/ai-kiosk/issues/17) | nice-to-have | Remove the `127.0.0.1:8001` fallback for non-local pages | — | open |
| 11 | [#18](https://github.com/23blocks-OS/ai-kiosk/issues/18) | nice-to-have | Delete two unused `lang` parameters | — | open |
| 12 | [#19](https://github.com/23blocks-OS/ai-kiosk/issues/19) | nice-to-have | Fix the broken link in `apps/website/index.html` | — | open |
| — | [#24](https://github.com/23blocks-OS/ai-kiosk/issues/24) | should-fix | Timeout shows "no local model connected", a false message (follow-up of #23) | — | done 2026-11-09 |
| — | [#28](https://github.com/23blocks-OS/ai-kiosk/issues/28) | should-fix | Logs too thin to diagnose failures (errors swallowed, no duration or outcome) | — | done 2026-11-09 |
| 13 | [#20](https://github.com/23blocks-OS/ai-kiosk/issues/20) | nice-to-have | Document the one-worker rule | — | open |

## Ideas (no issue yet)
- **Streaming for `/v1`.** Not supported now. Many OpenAI clients stream.
- **Whisper and Piper (voice)** are not installed on Aurelium.
- **CORS**, only if browser apps on other sites will call the API.
- **Cloudflare Access** on `aureliano.twofourai.com`. Optional now that keys exist.

## Done
- 2026-11-08 — Repo-root leak closed (PR #1). Selector (PR #2). Team API with keys (PR #3). Backend live on Aurelium.
- 2026-11-08 — `kiosk.ciaocorp.com` gets the app only (PR #4). Checked from outside: `/v1` is 404 there, even with a key.
- 2026-11-08 — Home button and idle reset (PR #6). Wiki (PR #5).
- 2026-11-08 — Kiosk STUB bug ([#23](https://github.com/23blocks-OS/ai-kiosk/issues/23)): switched to the instruct model. Checked from outside.
- 2026-11-08 — Apps are service users with keys ([#22](https://github.com/23blocks-OS/ai-kiosk/issues/22), PR #25, [spec](specs/issue-22-apps-as-service-users.md)). Checked from outside.
- 2026-11-08 — Record repo pushed to `3Metas/ciao-kiosk`.
