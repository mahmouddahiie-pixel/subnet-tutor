#!/usr/bin/env bash
# Install llama-bench for ADTC profiler (Ubuntu/Debian)
set -euo pipefail

echo "=== Install llama-bench for ADTC profiler ==="

if command -v llama-bench >/dev/null 2>&1; then
  echo "llama-bench already on PATH: $(which llama-bench)"
  llama-bench --help 2>&1 | head -3 || true
  exit 0
fi

echo ""
echo "Option A (recommended on Ubuntu): install from apt"
echo "  sudo apt update"
echo "  sudo apt install -y llama.cpp-tools"
echo ""

if command -v apt-get >/dev/null 2>&1; then
  echo "Attempting apt install (requires sudo password)..."
  sudo apt-get update -qq
  sudo apt-get install -y llama.cpp-tools
fi

if command -v llama-bench >/dev/null 2>&1; then
  echo "Success: $(which llama-bench)"
  exit 0
fi

echo ""
echo "Option B: build from source"
echo "  sudo apt install -y build-essential cmake git libssl-dev"
echo "  git clone https://github.com/ggml-org/llama.cpp ~/llama.cpp"
echo "  cd ~/llama.cpp && cmake -B build && cmake --build build -j\$(nproc)"
echo "  export PATH=\"\$HOME/llama.cpp/build/bin:\$PATH\""
echo ""
echo "Option C: download prebuilt binary (Ubuntu x64)"
echo "  See: https://github.com/ggml-org/llama.cpp/releases"
echo ""
exit 1
