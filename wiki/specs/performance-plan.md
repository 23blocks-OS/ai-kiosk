# Performance plan (draft, no code)

Status: draft, needs Juan's approval. Juan, 2026-11-09: "start planning, no code changes in the optimization for performance and can we start testing the api for direct agent consumption?"

## What I measured (Aurelium, 2026-11-09, model `qwen3-vl:4b-instruct`, 8 GB shared board)

| Case | Result |
| --- | --- |
| Warm, 11 tokens in, 5 out | 0.7 s |
| Warm, 21 in, 168 out | 12.9 s, 13 tok/s |
| Warm, 1,513 in, 80 out | 9.3 s |
| Warm, image + question (sales sample) | 7.7 s |
| 4 parallel tiny requests, 2 keys | 1.1 to 1.8 s each, 1.8 s total |
| First call after 5 idle minutes | 50 s, and one 504 at 90 s |
| 600-token output, 1.5k context | Ollama OOM-killed (`oom-kill`, 5.4 GB peak) |

Population: one run per row, one machine, tailnet-free path through Cloudflare for the first block, localhost for the rest. Not a benchmark.

## Problems, in order

1. **OOM kill** ([https://github.com/23blocks-OS/ai-kiosk/issues/49](https://github.com/23blocks-OS/ai-kiosk/issues/49)). Two kills today. Plan: cap `max_tokens` in the proxy (for example 512), cap input size, and lower the context. Check `OLLAMA_CONTEXT_LENGTH` and `OLLAMA_FLASH_ATTENTION` on the service (sudo). Measure peak memory before and after.
2. **Cold start after idle** ([https://github.com/23blocks-OS/ai-kiosk/issues/50](https://github.com/23blocks-OS/ai-kiosk/issues/50)). Plan: `OLLAMA_KEEP_ALIVE=-1` on the service (sudo), or a warm call every 4 minutes from the backend. Needs Juan for sudo.
3. **Speed.** 13 tok/s is the board's limit with 28% of the model on CPU. Options: a smaller quantization so it fits on GPU, or a smaller model for text-only calls. Each needs a quality check on the Raft and Intercambio questions first.
4. **Fair use** ([#9](https://github.com/23blocks-OS/ai-kiosk/issues/9)). The semaphore allows 2 calls. A visitor can still hold both. Rate-limit rule in Cloudflare, or a per-key limit in the backend.

## Not in this plan
No code until Juan approves. No change to the model.

## Result
Not built.
