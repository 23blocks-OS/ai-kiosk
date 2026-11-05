# Lifeboat as a fourth kiosk — evaluation

**Status: candidate, added 2026-11-05 at Juan's word. Not built, not ported.**

Source: our fork [23blocks-OS/lifeboat](https://github.com/23blocks-OS/lifeboat)
(fork of `johnpsasser/lifeboat`, MIT, HEAD `69b3ca1` at fork time).
Lifeboat is an offline emergency assistant for Apple Silicon Macs: a
local LLM + a 200 GB offline library (medicine, survival, Army/FEMA
manuals, repair, water/power/radio, all of English Wikipedia), with
cited answers and no internet at run time.

## Why it fits

- Same thesis as the other kiosks, in a different room. Intercambio
  is "help me with this paper, offline, in Spanish." Lifeboat is
  "help me when everything is down, offline, with sources." Small
  local model, no cloud, no account, data stays in the box, and the
  answer has to be useful to a real person in a real moment.
- Natural fourth kiosk in this monorepo: same Jetson shell, same
  agent + Picture-in-Picture layout, but the backend is Lifeboat's
  retrieval — cited steps from real manuals, not a model guessing.
  In Boulder County the story writes itself: wildfire, smoke, power
  outage, earthquake. A kiosk in a library or community center that
  works when the Wi-Fi doesn't.
- Fits the Mozilla Human-Scale AI logic (Small, Intentional,
  Tailored): a specific community, a small local model, control
  stays with the people using it.
- Safety culture we want to keep, not strip out: cited answers,
  "my sources don't cover this" instead of guessing, never invent a
  dose / dilution / wire size / plant ID, child-dose guard in code
  (not just in the prompt), danger warnings (shock, fire, carbon
  monoxide), and a printable binder of verbatim procedures.

## What Lifeboat is, in its own terms

- Chat model + embedding + reranker, all as `llama-server`
  processes on loopback (`127.0.0.1`: app 9110, chat 9120, embed
  9121, rerank 9122), `--offline`, no web UI from llama.cpp.
- Hybrid search: keyword (SQLite FTS5 / BM25) + meaning search
  (Qwen3-Embedding-0.6B, 1-bit vectors in sqlite-vec) + live
  Wikipedia search through the ZIM's Xapian index. A reranker
  (bge-reranker-v2-m3) picks the best 8 passages, max 2 per page.
- Household intake (ages, weights, conditions, medicines,
  allergies) and a region file (local hazards + local PDFs).
  Household data lives only in `household.json`, git-ignored.
- `verify-offline` proves nothing uses the network while answering
  15 test questions. `print` builds a paper binder of ~50 critical
  procedures with verbatim source text, no AI-written words.
- Repo is code only. The library is downloaded by `./lifeboat
  fetch` (~210 GB full, ~55 GB for groups 1+2+4 without full
  Wikipedia), then `./lifeboat index` (hours to days on a Mac).

## The question Juan asked: "there is no Linux / NVIDIA — is that not a model? What work is needed to have it NVIDIA-ready?"

Short answer: **right — it is not a model problem. The models are
portable. The platform / runtime is not.**

The models are GGUF files. The same GGUF file runs on Apple Metal,
on NVIDIA CUDA, or on CPU — the file does not care. What is
Mac-only is everything *around* the model: the installer, the
`llama-server` binary, the OS commands, and the model *sizes*
chosen for a 64 GB Mac. All of that is in our fork, and this is
what a Linux / NVIDIA (Jetson) port has to change. Evidence below
is from the forked code, file and line at fork time.

### 1. The installer refuses non-Mac hardware on purpose

`scripts/setup.sh:11`:

```bash
[ "$(uname -s)-$(uname -m)" = "Darwin-arm64" ] || { say "Lifeboat needs an Apple Silicon Mac."; exit 1; }
```

Port work: detect `Linux-aarch64` (Jetson) instead, and branch the
rest of setup on OS. This one line is the gate — everything after
it assumes macOS.

### 2. The llama.cpp binary is a macOS Metal build

`scripts/setup.sh:14-22` downloads a pinned llama.cpp release:

```
llama-$LLAMA_TAG-bin-macos-arm64.tar.gz   # Metal build
```

and then runs macOS-only `xattr -dr com.apple.quarantine`.

Port work: get a CUDA build of `llama-server` for Jetson ARM64.
Two routes:
- **Build llama.cpp from source on the Jetson** with CUDA enabled
  (`GGML_CUDA=ON`, JetPack's CUDA 13.2). Slow first build, then a
  pinned binary we can reuse. This keeps Lifeboat's `app/llm.py`
  unchanged — it just starts `bin/llama-server` and talks HTTP.
- **Or use Ollama**, which already ships a Jetson CUDA build and
  is what the ai-kiosk backend already uses. That is the shorter
  path for the kiosk, but it means changing `app/llm.py` (it
  starts three `llama-server` processes with `-ngl 999` and
  `--embedding` / `--reranking` flags) to call Ollama's
  `/api/embeddings`, `/api/chat`, and a reranker endpoint instead.
  The reranker has no Ollama equivalent out of the box — that
  piece still needs a `llama-server` (or a small FastAPI wrapper
  around it).

Either way, the *model files* do not change. The *server binary*
does.

### 3. Homebrew, `uv`, `aria2`, `open`, `caffeinate`, `/Volumes`

- `scripts/setup.sh:12,47` requires `uv` via `brew install uv`,
  and suggests `brew install aria2`. On Jetson Linux (Ubuntu
  24.04, JetPack 7.2) there is no Homebrew: `uv` installs via its
  own installer / pip, `aria2` via `apt`.
- The `lifeboat` control script uses macOS `open "$APP_URL"` to
  open the browser, and `caffeinate -is` to keep the Mac awake
  during `fetch` / `index`. Linux equivalents: `xdg-open` (or
  nothing — a kiosk opens Chromium itself) and
  `systemd-inhibit` (or nothing — a mains-powered kiosk does not
  sleep).
- External-drive paths are macOS-style (`/Volumes/MyDrive/...`,
  `scripts/setup.sh`, `README.md`). On the Jetson the 1 TB NVMe
  is the internal drive, mounted at a Linux path
  (`/media/...` or a fixed mount point) — the `data` symlink
  logic in `setup.sh` survives, the path does not.
- `xattr -dr com.apple.quarantine` (setup.sh) is macOS-only and
  is simply deleted on Linux.

### 4. Python dependencies on Linux ARM64

`requirements.txt` is small and mostly portable (FastAPI,
`uvicorn`, `httpx`, `pypdf`, `selectolax`), but two are the risk:
`libzim` (reads ZIM archives) and `sqlite-vec` (vector search).
Both need Linux ARM64 wheels, or a build from source, in the
offline `vendor/wheels` flow (`setup.sh` saves wheels so the venv
can be rebuilt with no internet). This has to be verified on the
Jetson, not assumed. Python itself is 3.12 via `uv`, same as Mac.

### 5. Model sizing — the real Jetson problem

`app/config.py`, `PROFILES` (at fork time):

| Profile | Model | File | Context |
|---|---|---|---|
| `battery` (default) | Qwen3.6 35B-A3B, Q6_K | 29 GB | 32768 |
| `best` | Qwen3.8 27B, Q8_0 | 29 GB | 32768 |
| `tiny` | Gemma 4 E4B, Q4_0 | 5 GB | 16384 |

Helpers, always on: Qwen3-Embedding-0.6B + bge-reranker-v2-m3,
~1.5 GB together.

Our Jetson has **8 GB total, shared CPU + GPU**. The 29 GB
profiles cannot load, full stop — not slow, impossible. `tiny`
(5 GB) fits, but Lifeboat's own README calls it the least
accurate, and its child-dose testing showed the bigger models
were the careful ones.

Port work: define a new Jetson profile, and re-test quality —
especially the cited-answer and child-dose behaviour — at that
size. Candidates, not decisions:
- Qwen3-VL 4B (3.3 GB, the kiosk's existing model) as the chat
  model, so the emergency kiosk shares the Intercambio model.
- Or a Qwen3 4B / 8B text model (Q4_K_M) for chat, keeping the
  same embedding + reranker helpers.
- Cut context from 32768 to 4096 / 8192 (context costs memory,
  not speed, and 8 passages + a question do not need 32k).
- Keep the safety rules and the child-dose guard in code — do
  not trade them away for size.

### 6. Library slice, not the whole 200 GB on day one

The full library fits our 1 TB SSD, but `fetch` is 2–4 hours and
`index` is hours to days (Mac: ~60 passages/s; a helper GPU
does ~280/s). Port work: start with the core groups
(`./lifeboat fetch 1 2 4`, ~55 GB: base models + core archives +
PDFs), skip full Wikipedia (119 GB) until the core works, and
write a Boulder region file (`regions/boulder.json`: wildfire,
smoke, extreme heat, flash flood, winter storm, power outage)
with local PDFs (county evacuation guide, Ready-Set-Go) instead
of the Los Angeles default. Spanish sources are a later step —
the library as forked is English.

### 7. Kiosk adaptation (after the port works)

Lifeboat's web page (`127.0.0.1:9110`) is a laptop chat page:
model menu, Load/Unload, Think harder, Search library, Quick
topics, Sources. A kiosk needs the ai-kiosk shell instead:
- Agent + PiP (waveform first), big touch targets, ES-first
  with an EN toggle, one big mic button, short plain-language
  answers read aloud.
- No household intake on the shared kiosk by default (that file
  holds health data — on a public kiosk it must be opt-in per
  session and wiped at session end, or omitted entirely).
- `verify-offline` re-run on the Jetson: loopback-only sockets,
  no outside URLs in the page, 15 test questions, same as Mac.
- Power is different: a MacBook on battery is Lifeboat's design
  centre (unload the model, Low Power Mode, solar). A kiosk is
  mains-powered at 25 W — the power story becomes "always on,
  always ready," not battery life.

## Open items (not decided)

- Port route: build llama.cpp/CUDA from source, or Ollama +
  a reranker server? (Ollama is shorter for the kiosk; source
  build keeps Lifeboat's `llm.py` untouched.)
- Jetson chat-model profile: Qwen3-VL 4B shared with Intercambio,
  or a separate text model? Quality re-test required either way.
- Library slice for the first test, and whether Spanish sources
  are in scope for v1 or later.
- Pilot location: same community-center / library shape as
  Intercambio, or a different partner (Boulder County emergency
  preparedness, a library, a shelter)?
- Household intake on a shared kiosk: per-session opt-in with
  wipe, or omitted in v1?
- Mozilla: Lifeboat-as-kiosk is a candidate story, not a filing
  decision. First-stage proposal deadline, if pursued, is
  Nov 20, 2026 — same as the other kiosk candidates.
