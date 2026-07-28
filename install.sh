#!/usr/bin/env bash
# One-command install for Subnet Tutor (Ubuntu/Debian)
set -euo pipefail
cd "$(dirname "$0")"

echo "============================================"
echo "  Subnet Tutor — Easy Install"
echo "============================================"
echo

# System deps
if ! command -v python3 >/dev/null; then
  echo "ERROR: python3 not found. Install: sudo apt install python3"
  exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "Installing python3-venv..."
  sudo apt-get update -qq
  sudo apt-get install -y python3-venv python3-pip
fi

# Virtual environment
if [[ ! -d .venv ]]; then
  echo "[1/4] Creating virtual environment..."
  python3 -m venv .venv
else
  echo "[1/4] Virtual environment exists."
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[2/4] Installing Python packages (may take a few minutes)..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "[3/4] Building knowledge index..."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
python -m app.rag.indexer

echo "[4/4] Downloading AI model (~1.1 GB, needs internet once)..."
if [[ -f model/qwen2.5-1.5b-instruct-q4_k_m.gguf ]]; then
  echo "  Model already downloaded."
else
  bash download_model.sh
fi

echo
echo "============================================"
echo "  Install complete!"
echo "============================================"
echo
echo "Start the app:"
echo "  bash run.sh"
echo
echo "Open in browser:"
echo "  http://127.0.0.1:8765"
echo
echo "Wait ~1-2 min for footer to show 'LLM ready'."
echo
echo "If LLM fails on this machine:"
echo "  bash scripts/diagnose_llm.sh"
echo
