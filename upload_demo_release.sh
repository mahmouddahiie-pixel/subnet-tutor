#!/usr/bin/env bash
# Upload demo video to GitHub Release (optional hosting for DevPost video link)
set -euo pipefail
cd "$(dirname "$0")"

VIDEO="demo_output/subnet-tutor-demo.mp4"
if [[ ! -f "$VIDEO" ]]; then
  echo "Run first: bash automate_submission.sh"
  exit 1
fi

gh release create v1.0.0-demo \
  "$VIDEO" \
  screenshots/home-en.png \
  screenshots/tutorial-fingers.png \
  screenshots/game-level1.png \
  screenshots/tutorial-ar.png \
  --title "ADTC 2026 Demo Video" \
  --notes "Demo video for DevPost. Download MP4 and upload to YouTube, or use release URL if DevPost accepts direct links."

echo ""
echo "Release URL:"
gh release view v1.0.0-demo --json url -q .url
echo ""
echo "Direct MP4 download (use as video link if DevPost allows file URL):"
gh release view v1.0.0-demo --json assets -q '.assets[] | select(.name | endswith(".mp4")) | .url'
