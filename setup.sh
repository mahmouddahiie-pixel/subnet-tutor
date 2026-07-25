#!/usr/bin/env bash
# Setup script for Subnet Tutor (requires python3-venv and pip)
set -euo pipefail
cd "$(dirname "$0")"

if ! python3 -m venv .venv 2>/dev/null; then
  echo "Install python3-venv first: sudo apt install python3-venv python3-pip"
  exit 1
fi

source .venv/bin/activate
pip install -r requirements.txt
python -m app.rag.indexer
echo "Setup complete. Run: bash run.sh"
