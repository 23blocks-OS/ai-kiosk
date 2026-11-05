# Plan — Intercambio first

**Build order decided 2026-11-04: Intercambio first.** Shop and
Nonprofit are later, not cancelled.

## The situation

Spanish-speaking newcomers in Boulder County need help with paper:
forms, letters from schools and agencies, appointment notices. The
help today is a person at a desk, when one is available. A kiosk in
the community center that reads the paper and explains it — in
Spanish, patiently, as many times as needed — fills the gaps.

## The kiosk

- One Jetson box + touchscreen + USB webcam, in the community center.
- The visitor puts a form or letter under the camera. The small
  Picture-in-Picture window shows exactly what the agent sees.
- The agent reads it, explains what it says, translates words or
  whole sections, and helps with the next step: what to fill in,
  where to go, what to bring, how to book an appointment.

## Language

Bilingual, **Spanish-first**. The interface defaults to Spanish, with
a big ES/EN toggle. The agent answers in the language the visitor
used.

## Scope — what it does

- Read a document under the camera (OCR + explanation).
- Explain and translate forms, letters, and notices.
- Help navigate local services and appointments (where, when, what
  to bring, how to book).

## Scope — what it does NOT do

- **Not legal advice.** It explains what a paper says; it does not
  advise on immigration status, rights, or legal strategy. When a
  question is legal, it says so and points to a person.
- No accounts, no sign-in, no tracking, no recording.
- Nothing leaves the box. No cloud, no phone-home.

## Why this one first

- The pilot partner exists: Juan built Intercambio's app and served
  on its board (chair 2021–2022). The relationship is real.
- The task fits the hardware: one document, one conversation, one
  4B vision model — no screen-driving, no fleet, no cluster.
- It is the strongest fit for a human-scale grant story: a specific
  community, a small local model, and control that stays with the
  people using it.

## Agent visual

Phase 1 (built): an animated waveform/orb — see
`docs/agent-visual-roadmap.md`. Phase 2 (simple mascot) and Phase 3
(friendly face avatar) are planned, not built, in that order.

## Saturday test (Nov 7, 2026)

1. Boot the Jetson, open the Intercambio app in full-screen Chromium.
2. USB webcam on, sample form under it. PiP must show the document
   clearly; Freeze must capture a readable frame.
3. Install Qwen3-VL 4B, replace the canned reply with a real read of
   the frozen frame, in Spanish.
4. Voice: mic → Whisper → model → Piper → speaker.

## Open items (not decided)

- Pilot location and hours inside Intercambio (not yet agreed with them).
- Which sample forms to test first.
- Whether the Pi camera (CSI) replaces the USB webcam later.
- Mozilla first-stage proposal: build-first decision only — filing
  the proposal is a separate decision, deadline Nov 20, 2026.
