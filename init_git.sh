#!/usr/bin/env bash
# Initialize git repo for ADTC submission (run after: sudo apt install git)
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v git >/dev/null 2>&1; then
  echo "Install git first: sudo apt install git"
  exit 1
fi

git init
git add .
echo ""
echo "Staged files (verify NO .gguf):"
git status --short | head -40
echo ""
if git status --short | grep -q '\.gguf'; then
  echo "ERROR: .gguf file staged! Check .gitignore"
  exit 1
fi
echo "OK — no GGUF in staging area."
echo ""
echo "Next:"
echo "  git commit -m \"Subnet Tutor — ADTC 2026 submission\""
echo "  git remote add origin https://github.com/mahmouddahiie-pixel/subnet-tutor.git"
echo "  git push -u origin main"
