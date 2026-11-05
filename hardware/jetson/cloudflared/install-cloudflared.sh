#!/usr/bin/env bash
# Install cloudflared (ARM64) on the Jetson. Install only — it does
# NOT log in, create a tunnel, or start anything, because those steps
# need a human in the Cloudflare dashboard (see README.md in this
# folder). It contains no token and accepts none.
#
# Usage: ./install-cloudflared.sh
set -euo pipefail

# Refuse to run with any token-like argument or environment variable.
# Tokens are created in the Cloudflare dashboard, never passed here.
if [ "$#" -gt 0 ]; then
  echo "ERROR: do not pass arguments (and never a token) to this script." >&2
  echo "Run it with no arguments, then follow the manual steps in README.md." >&2
  exit 1
fi
if [ -n "${CLOUDFLARE_TOKEN:-}" ] || [ -n "${TUNNEL_TOKEN:-}" ]; then
  echo "ERROR: CLOUDFLARE_TOKEN / TUNNEL_TOKEN is set in this shell." >&2
  echo "Unset it and run this script with no token present." >&2
  exit 1
fi

# ARM64 .deb from Cloudflare (Jetson Orin Nano is aarch64).
curl -fsSL -o /tmp/cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i /tmp/cloudflared.deb
rm -f /tmp/cloudflared.deb
cloudflared --version

cat <<'EOF'

cloudflared is installed. Next, by hand (see README.md in this folder):
  1. cloudflared tunnel login        (opens a browser; pick the Cloudflare account)
  2. cloudflared tunnel create ai-kiosk
  3. Copy config.yml.example to ~/.cloudflared/config.yml and fill in
     your tunnel id and chosen hostname — placeholders only in the repo.
  4. In Cloudflare Zero Trust -> Networks -> Tunnels, add the Public
     Hostname for your tunnel (hostname -> http://localhost:8000).
  5. cloudflared tunnel run ai-kiosk
  6. Open the https:// link and check the Intercambio app loads.
EOF
