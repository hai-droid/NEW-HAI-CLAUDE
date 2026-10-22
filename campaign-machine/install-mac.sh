#!/usr/bin/env bash
# Campaign Machine – Mac setup. Run from Terminal:  bash install-mac.sh
set -e
cd "$(dirname "$0")"
echo "=== Campaign Machine – Mac setup ==="

if ! command -v python3 >/dev/null; then
  echo "Python 3 is missing. Install it from https://www.python.org/downloads/ and run this again."
  exit 1
fi
if ! command -v node >/dev/null; then
  echo "Node.js is missing (needed for Vercel deploys). Install the LTS from https://nodejs.org and run this again."
  exit 1
fi
if ! command -v git >/dev/null; then
  echo "Installing Apple command line tools (git)…"
  xcode-select --install || true
fi
if ! command -v claude >/dev/null; then
  echo "Installing Claude Code…"
  curl -fsSL https://claude.ai/install.sh | bash
fi

echo "Installing Python packages…"
if ! python3 -m pip install --user -r requirements.txt; then
  echo "pip refused (Homebrew Python). Creating a local virtual environment instead…"
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  echo "→ Before running claude, run: source .venv/bin/activate"
fi

[ -f .env ] || cp .env.example .env

echo
echo "=== Done ==="
echo "1. open -e .env   → fill in the keys (see README)"
echo "2. claude          → starts Claude Code in this folder"
echo "3. /campaign demo-studio"
