# shared-ui

Styles shared by every kiosk in this monorepo. Kiosk pages link to these
files with relative paths (`../../packages/shared-ui/...`) and serve from
the repo root, so there is no build step and no duplication.

- `pip.css` — the Picture-in-Picture window: what the agent is seeing.
- `agent.css` — the agent main view: status, conversation, controls.

Kiosk-specific layout and colour live in each app's own `styles.css`.
