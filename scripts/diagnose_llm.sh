#!/usr/bin/env bash
# Diagnose why the on-device LLM is not loading on this machine.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Subnet Tutor LLM diagnostics ==="
echo "Project: $ROOT"
echo

MODEL_PATH="${SUBNET_TUTOR_MODEL_PATH:-$ROOT/model/qwen2.5-1.5b-instruct-q4_k_m.gguf}"
echo "Model path: $MODEL_PATH"

if [[ -f "$MODEL_PATH" ]]; then
  ls -lh "$MODEL_PATH"
else
  echo "ERROR: Model file missing."
  echo "Fix: bash download_model.sh"
  exit 1
fi
echo

if [[ -d "$ROOT/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
  echo "Using venv: $ROOT/.venv"
else
  echo "WARNING: No .venv found. Run: bash setup.sh"
fi
echo

echo "--- Python / llama-cpp-python ---"
python3 -V || true
python3 -c "
try:
    import llama_cpp
    print('llama_cpp: OK', getattr(llama_cpp, '__version__', 'unknown'))
except ImportError as e:
    print('llama_cpp: MISSING —', e)
    print('Fix: pip install llama-cpp-python')
    raise SystemExit(1)
" || exit 1
echo

echo "--- Memory ---"
free -h 2>/dev/null || true
echo

echo "--- Try loading model (may take 1–2 min) ---"
SUBNET_TUTOR_MODEL_PATH="$MODEL_PATH" python3 <<PY
import os
import sys
from pathlib import Path

ROOT = Path("$ROOT")
sys.path.insert(0, str(ROOT))

model_path = os.environ.get("SUBNET_TUTOR_MODEL_PATH", str(ROOT / "model" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"))

try:
    from llama_cpp import Llama
    print(f"Loading: {model_path}")
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=max(2, (os.cpu_count() or 4) - 1),
        use_mmap=True,
        verbose=False,
    )
    out = llm("Say OK in one word.", max_tokens=8, temperature=0)
    text = out["choices"][0]["text"].strip()
    print("Load: SUCCESS")
    print("Sample output:", text[:80])
except Exception as exc:
    print("Load: FAILED")
    print("Error:", exc)
    sys.exit(1)
PY

echo
echo "=== All checks passed — restart the app: bash run.sh ==="
