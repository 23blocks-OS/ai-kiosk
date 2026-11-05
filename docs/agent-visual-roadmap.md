# Agent visual roadmap

The agent's face, in Juan's order. Phase 1 is built; Phases 2 and 3
are planned, not built.

## Phase 1 — Animated waveform / orb (built)

- **What it is:** a soft glowing orb with waveform bars, plain
  HTML/CSS/SVG + a little vanilla JS. No framework, no external
  assets, no network calls, no emoji. It runs entirely on the Jetson,
  offline.
- **States** (always paired with the visible status text — the
  animation is never the only indicator):
  - Idle: slow calm breathing pulse.
  - Listening: waveform ripples; when the browser grants a mic
    audio stream, a real analyser level stretches the bars — if no
    level is available, it is a gentle ripple, never a fake meter.
  - Thinking: slow spin ring + pulse while the backend works.
  - Speaking: rhythmic waveform while the reply is spoken/shown.
- **PiP glance:** when a PiP frame is frozen to read a document (or
  the agent is thinking about an uploaded photo), the orb shifts
  subtly toward the PiP, then back when it answers.
- **Accessibility:** `prefers-reduced-motion` falls back to a static
  orb + status text. High contrast, large touch targets unchanged.
- **Identity:** none. The orb is deliberately not a person.

## Phase 2 — Simple mascot character (next, not built)

- **What it is:** a flat illustrated character — big eyes, simple
  expressions, no attempt to look real. Cheap browser animation
  (CSS/SVG, same stack as the orb).
- **What changes:** the orb is replaced by the character; its eyes
  look at the PiP when reading a document and back at the visitor
  when answering; it smiles when it understands, tilts its head
  when unsure.
- **What stays the same:** states (idle/listening/thinking/
  speaking), transcript, PiP, backend, prompts, privacy rules.
- **Decide before starting:** the character design/illustration
  (who draws it, what it looks like, name), its expression set, and
  whether it is one static SVG with animated eyes or a small set of
  poses. The `agentVisual` switch in `app.js` already has a
  `mascot` value — today it shows a "coming soon" panel, never a
  fake mascot.

## Phase 3 — Friendly face avatar (final, most complex, not built)

- **What it is:** a human-like face with lip-sync that looks at the
  visitor, nods, and speaks.
- **What changes:** the visual becomes a video/avatar surface; the
  states stay the same, but speaking now needs real lip-sync timing
  from the TTS audio.
- **What stays the same:** states, transcript, PiP, backend, prompts.
- **Decide before starting:** vendor vs local engine (a cloud avatar
  service such as Anam, audio-passthrough only, vs a local avatar
  engine), the voice, the identity (its own distinct face and name
  for the Intercambio agent), cost, and privacy (cloud avatar
  services need internet and send audio out — that breaks the
  "nothing leaves the box" rule unless the audio path is explicitly
  approved).
- **Identity rule (hard):** the face must be its own distinct face
  for this agent. **NEVER Lola.** Lola is her own agent with her own
  brain; outside platforms supply animation only for her. This
  agent is separate. The `agentVisual` switch already has a `face`
  value — today it shows a "coming soon" panel, never a fake face.
- **Risks:** uncanny valley and raised expectations — a face that
  looks human makes people expect human understanding, and they get
  frustrated faster when it falls short; plus cost and latency of a
  cloud round-trip per turn.

## Why this order

Waveform first proves the real job (reading forms) without the face
distracting from it, and it works offline on the Jetson today.
The mascot adds warmth without pretending to be human. The face is
the warmest and the heaviest, so it comes last, only if the first
two prove the agent is useful.
