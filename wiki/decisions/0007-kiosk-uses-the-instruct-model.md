# 0007 — The kiosk uses `qwen3-vl:4b-instruct`

- **Date:** 2026-11-08. **Status:** accepted, live. **Issue:** [#23](https://github.com/23blocks-OS/ai-kiosk/issues/23) (closed).
- **Context:** Juan reported that the kiosk answered "STUB — no local model connected yet". The model was connected. `qwen3-vl:4b` is a reasoning model: about 1,260 tokens of hidden reasoning for a two-sentence answer. With the model partly on CPU (memory is tight), replies took 100 to 200 seconds. The backend stops waiting at 120 seconds and shows the stub.
- **Decision:** the service runs with `OLLAMA_MODEL=qwen3-vl:4b-instruct`. It does not reason. Same question: 7 s warm, 18 s with a model swap, 87 to 99 tokens.
- **Checked from outside, 2026-11-08:** `/api/chat` 5 s; `/api/vision` with a screenshot 42 s and the text read correctly.
- **Consequence:** `/v1` users can still ask for `qwen3-vl:4b`. Tell testers to use the instruct model for quick answers. Only one model fits in memory, so asking for the other one unloads the first.
- **Open:** the stub text is still false when the model only timed out: [#24](https://github.com/23blocks-OS/ai-kiosk/issues/24).
