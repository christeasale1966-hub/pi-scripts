#!/usr/bin/env bash
set -euo pipefail
if [[ "${EUID}" -eq 0 ]]; then
  echo 'Run this as sensor, not with sudo. Only apt commands request sudo.' >&2
  exit 2
fi
SRC="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/grok-bot"
# Raspberry Pi OS / Debian: OS packages stay managed by apt, SDK by venv.
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
mkdir -p "$DEST"
if [[ "$SRC" != "$DEST" ]]; then
  for f in grok_text.py grok README.md install.sh; do
    if [[ -e "$DEST/$f" ]]; then
      echo "Refusing to overwrite existing $DEST/$f. Review it first." >&2
      exit 2
    fi
  done
  for f in grok_text.py grok README.md install.sh; do cp -- "$SRC/$f" "$DEST/$f"; done
fi
python3 -m venv "$DEST/.venv"
"$DEST/.venv/bin/python" -m pip install --upgrade pip
"$DEST/.venv/bin/python" -m pip install xai-sdk
chmod 755 "$DEST/grok"
echo "Installed text client at $DEST. No API requests made. Read $DEST/README.md for private key setup."
