#!/usr/bin/env bash
# One-command automation: demo video + DevPost prep
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Subnet Tutor — Automated Demo & DevPost Prep ==="

source .venv/bin/activate 2>/dev/null || true

echo "[1/4] Installing capture dependencies..."
pip install -q -r requirements-dev.txt playwright imageio imageio-ffmpeg pillow 2>/dev/null || pip install -r requirements-dev.txt
python -m playwright install chromium 2>&1 | tail -3

echo "[2/4] Generating demo video from automated browser capture..."
PYTHONPATH=. python scripts/generate_demo_video.py

echo "[3/4] Copying screenshots for DevPost..."
mkdir -p screenshots
cp demo_output/frames/00_home_en.png screenshots/home-en.png 2>/dev/null || true
cp demo_output/frames/03_tutorial_fingers.png screenshots/tutorial-fingers.png 2>/dev/null || true
cp demo_output/frames/06_game_level1.png screenshots/game-level1.png 2>/dev/null || true
cp demo_output/frames/05_tutorial_ar.png screenshots/tutorial-ar.png 2>/dev/null || true

echo "[4/4] Opening DevPost submission page..."
VIDEO_PATH="$(pwd)/demo_output/subnet-tutor-demo.mp4"
echo ""
echo "============================================"
echo "  AUTOMATION COMPLETE"
echo "============================================"
echo "  Video:  $VIDEO_PATH"
echo "  Screenshots: screenshots/"
echo "  DevPost guide: DEVPOST_SUBMISSION.md"
echo ""
echo "  MANUAL STEPS (require your login):"
echo "  1. Upload $VIDEO_PATH to YouTube (unlisted)"
echo "  2. Open: https://adtc-2026.devpost.com/project/submissions/new"
echo "  3. Paste content from DEVPOST_SUBMISSION.md"
echo "  4. GitHub: https://github.com/mahmouddahiie-pixel/subnet-tutor"
echo "============================================"

# DevPost must be submitted manually while logged in — see DEVPOST_SUBMISSION.md
