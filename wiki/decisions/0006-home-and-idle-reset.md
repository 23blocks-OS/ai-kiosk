# 0006 — Home button and idle reset

- **Date:** 2026-11-08. **Status:** accepted, live. **PR:** #6.
- **Context:** A shared kiosk must not keep one visitor's chat, photo or language for the next visitor. Rule from the README: nothing is recorded or stored.
- **Decision:** An "Inicio / Home" button returns to the selector. After 180 s with no touch (`?idle=N` changes it) the kiosk returns to the selector by itself. Leaving the page stops the camera and clears the chat and photo. The language resets too. The reset waits while the agent is thinking or listening.
- **Why a page change:** the page stores nothing, so navigation is the cleanest wipe. No state to track or forget.
- **Checked in a browser, 2026-11-08:** idle 3 s returned to the selector; a touch at 4 s with idle 6 s kept the page open.
- **Side effect:** the selector now uses the kiosk's cream and green look.
