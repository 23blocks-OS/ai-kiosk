# Kiosk — Lifeboat / Emergency (candidate, stub)

A fourth kiosk type, added 2026-11-05 as a candidate: an offline
emergency-preparedness kiosk, based on our fork
[23blocks-OS/lifeboat](https://github.com/23blocks-OS/lifeboat)
(fork of `johnpsasser/lifeboat`, MIT).

The idea: same Jetson shell as Intercambio, same agent +
Picture-in-Picture layout, but the backend is Lifeboat's retrieval
— cited steps from real manuals (medicine, survival, Army/FEMA,
repair, water/power/radio), not a model guessing. It works when the
Wi-Fi doesn't. In Boulder County: wildfire, smoke, power outage,
earthquake.

Picture-in-Picture source: **the source passage the agent is
reading from** (Lifeboat shows its work — every claim cited).

Status: **candidate / stub, not built, not ported.** Lifeboat as
forked is Apple Silicon Mac only; the Linux / NVIDIA port is the
open work. Full evaluation, including exactly what that port
has to change, is in `docs/lifeboat-eval.md`.

The Intercambio prototype (`../kiosk-intercambio/`) is the working
reference implementation for the kiosk shell.
