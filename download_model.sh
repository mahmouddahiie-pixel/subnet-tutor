#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR="$(dirname "$0")/model"
MODEL_FILE="${MODEL_DIR}/qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"

mkdir -p "${MODEL_DIR}"

if [[ -f "${MODEL_FILE}" ]]; then
  echo "Model already exists at ${MODEL_FILE}"
  exit 0
fi

echo "Downloading Qwen2.5-1.5B-Instruct Q4_K_M to ${MODEL_FILE}..."
if command -v curl >/dev/null 2>&1; then
  curl -L --fail --retry 3 -o "${MODEL_FILE}" "${MODEL_URL}"
elif command -v wget >/dev/null 2>&1; then
  wget -O "${MODEL_FILE}" "${MODEL_URL}"
else
  echo "Error: curl or wget required to download model weights." >&2
  exit 1
fi

echo "Download complete."
