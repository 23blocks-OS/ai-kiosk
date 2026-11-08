# 0003 — Team API with API keys

- **Date:** 2026-11-08. **Status:** accepted. **PR:** #3.
- **Context:** Juan wants a local inference engine that the team and other agents can call to try text and images and learn about local models.
- **Decision:** `GET /v1/models` and `POST /v1/chat/completions` pass through to Ollama's OpenAI-compatible API. Any installed model. No streaming. The 2-call GPU limit is shared with the kiosk.
- **Juan's words:** "all the tailnet users and agents need an apikey" and users from the Cloudflare tunnel need one too. "this should be a simple demo, not rocket science."
- **Keys:** a list of `name: key` in `services/agent-backend/api-keys.json`, read on every request. No file means the API is closed.
- **Deviation, on purpose:** Juan said "in the project itself". The file is in the project folder but **gitignored**. A committed key stays in git history forever. `api-keys.example.json` shows the shape. Juan can override.
- **Order of checks (Juan, 2026-11-08):** "all calls to the api need an api key validation before hitting the LLM ollama." The key is checked first: before the queue, before reading the body, before any call to Ollama. A test proves no HTTP client toward Ollama is opened without a valid key.
- **Not covered by keys:** the kiosk page's own `/api/*` and `/health`. A public page cannot hold a secret. The 2-call limit is the only protection there.
