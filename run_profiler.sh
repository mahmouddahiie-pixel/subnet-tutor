#!/usr/bin/env bash
# Run ADTC profiler (requires pip + llama-bench on PATH)
set -euo pipefail
cd "$(dirname "$0")"

echo "=== ADTC Profiler ==="

if ! command -v llama-bench >/dev/null 2>&1; then
  echo ""
  echo "ERROR: llama-bench not found on PATH."
  echo ""
  echo "Install it first:"
  echo "  bash install_llama_bench.sh"
  echo ""
  echo "Or manually:"
  echo "  sudo apt update && sudo apt install -y llama.cpp-tools"
  echo ""
  exit 1
fi

echo "llama-bench: $(which llama-bench)"
echo "Ensure dependencies: pip install -r requirements.txt"
echo "Ensure model: bash download_model.sh"
echo ""

if ! command -v adtc-profiler >/dev/null 2>&1; then
  echo "Installing adtc-profiler..."
  pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"
fi

bash download_model.sh

adtc-profiler run \
  --submission . \
  --mode participant \
  --output submission.json \
  --skip-accuracy

echo ""
echo "Report written to submission.json"
python3 -c "
import json
r = json.load(open('submission.json'))
print('measured_on:', r.get('environment', {}).get('measured_on'))
print('peak_rss_mb:', r.get('memory', {}).get('peak_rss_mb'))
print('tokens_per_second:', r.get('throughput', {}).get('tokens_per_second_generation'))
print('throttled:', r.get('cpu_thermal', {}).get('throttled'))
" 2>/dev/null || cat submission.json
