#!/usr/bin/env bash
# Validate ADTC submission file structure
set -euo pipefail
cd "$(dirname "$0")"

required=(
  metadata.json
  download_model.sh
  REPORT.md
  requirements.txt
  app/main.py
  app/llm/client.py
  app/rag/retriever.py
  knowledge/finger_method_en.md
  knowledge/finger_method_ar.md
)

missing=0
for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "MISSING: $f"
    missing=1
  fi
done

python3 -c "import json; json.load(open('metadata.json'))" && echo "metadata.json: valid JSON"
python3 -c "
import json
m = json.load(open('metadata.json'))
assert m['domain'] == 'math_scientific_reasoning'
assert 'en' in m['language_scope'] and 'ar' in m['language_scope']
assert len(m['test_prompts']) == 2
print('metadata.json: ADTC fields OK')
"

if [[ $missing -eq 0 ]]; then
  echo "All required files present."
else
  exit 1
fi
