#!/usr/bin/env python3
"""
Automated ADTC demo capture: screenshots + MP4 slideshow.
Requires: pip install playwright imageio imageio-ffmpeg
         playwright install chromium
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "demo_output"
SCREENSHOTS = OUT_DIR / "frames"
BASE_URL = "http://127.0.0.1:8765"


def ensure_server() -> None:
    import urllib.request

    try:
        urllib.request.urlopen(BASE_URL, timeout=2)
        print(f"Server OK: {BASE_URL}")
        return
    except Exception:
        pass
    print("Starting Flask server...")
    subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        cwd=ROOT,
        env={**dict(subprocess.os.environ), "PYTHONPATH": str(ROOT)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        try:
            urllib.request.urlopen(BASE_URL, timeout=2)
            print("Server started.")
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Could not start server on port 8765")


def capture_frames() -> list[Path]:
    from playwright.sync_api import sync_playwright

    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    idx = 0

    def shot(page, name: str, wait_ms: int = 800) -> None:
        nonlocal idx
        page.wait_for_timeout(wait_ms)
        path = SCREENSHOTS / f"{idx:02d}_{name}.png"
        page.screenshot(path=str(path), full_page=False)
        frames.append(path)
        idx += 1
        print(f"  captured {path.name}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        # Home EN
        page.goto(BASE_URL)
        shot(page, "home_en", 1200)

        # Tutorial - go to step 2 (Powers of Two) where finger buttons are visible
        page.goto(f"{BASE_URL}/tutorial")
        shot(page, "tutorial_intro", 1000)
        # Activate step 2 (finger interactive panel)
        step2 = page.locator(".step-tab").nth(1)
        if step2.count():
            step2.click()
            page.wait_for_timeout(600)
        for _ in range(3):
            btn = page.locator(".step-content.active .finger-btn[data-action='raise']")
            if btn.count():
                btn.click(timeout=5000)
                page.wait_for_timeout(400)
        shot(page, "tutorial_fingers", 1000)

        # Explain on active step
        explain = page.locator(".step-content.active .explain-btn").first
        if explain.count():
            explain.click()
            page.wait_for_timeout(3000)
        shot(page, "tutorial_explain", 500)

        # Arabic
        page.locator('button[data-lang="ar"]').click()
        page.wait_for_timeout(1500)
        shot(page, "tutorial_ar", 1000)

        # Game
        page.goto(f"{BASE_URL}/game?level=1")
        shot(page, "game_level1", 1000)

        page.locator("#answer-fingers").fill("3")
        page.locator("#answer-prefix").fill("27")
        page.locator("#submit-game").click()
        page.wait_for_timeout(1500)
        shot(page, "game_success", 1000)

        # Home AR footer
        page.goto(BASE_URL)
        shot(page, "home_ar", 1000)

        browser.close()

    return frames


def build_video(fps: int = 0.5) -> Path:
    """Build MP4 from PNG frames (~2 sec per frame at 0.5 fps)."""
    import imageio
    from PIL import Image

    frames = sorted(SCREENSHOTS.glob("*.png"))
    if not frames:
        raise RuntimeError("No frames captured")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    video_path = OUT_DIR / "subnet-tutor-demo.mp4"

    duration_per_frame = 1.0 / fps if fps > 0 else 2.0
    target_fps = 24
    repeats = max(1, int(duration_per_frame * target_fps))

    writer = imageio.get_writer(str(video_path), fps=target_fps, codec="libx264", quality=8)
    for fp in frames:
        img = Image.open(fp).convert("RGB")
        import numpy as np
        arr = np.array(img)
        for _ in range(repeats):
            writer.append_data(arr)
    writer.close()

    total_sec = len(frames) * duration_per_frame
    print(f"Video written: {video_path} ({len(frames)} scenes, ~{total_sec:.0f}s)")
    return video_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-capture", action="store_true")
    parser.add_argument("--fps", type=float, default=0.4, help="Scenes per second (0.4 ≈ 2.5s per frame)")
    args = parser.parse_args()

    ensure_server()

    if not args.skip_capture:
        print("Capturing browser frames...")
        capture_frames()

    print("Building MP4...")
    video = build_video(fps=args.fps)
    print(f"\nDone!\n  Video: {video}\n  Frames: {SCREENSHOTS}/")
    print("\nNext: Upload demo_output/subnet-tutor-demo.mp4 to YouTube (unlisted)")
    print("Then: open DEVPOST_SUBMISSION.md and submit on DevPost")


if __name__ == "__main__":
    main()
