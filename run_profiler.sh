#!/usr/bin/env bash
# Run ADTC profiler (requires pip + llama-bench on PATH)
set -euo pipefail
cd "$(dirname "$0")"

echo "=== ADTC Profiler ==="
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
python3 -c "import json; r=json.load(open('submission.json')); print(json.dumps({k:r.get(k) for k in ['measured_on','peak_ram_mb','tokens_per_second'] if k in r}, indent=2))" 2>/dev/null || cat submission.json
