# Demo Recording — Step by Step

Follow this guide to record your ≤2 minute ADTC demo video.

---

## Part 1 — Prepare (5 min)

### 1. Start the app and wait for model

```bash
cd ~/Projects/subnet-tutor
source .venv/bin/activate
bash run.sh
```

Wait until footer shows **"LLM ready"** (~1–2 min first time).

### 2. Open browser

- URL: http://127.0.0.1:8765
- Full screen or 1280×720 window
- Close unrelated tabs

### 3. Choose recording tool (Ubuntu)

| Tool | How to start |
|------|----------------|
| **OBS Studio** (best) | `sudo apt install obs-studio` → Screen Capture |
| **SimpleScreenRecorder** | `sudo apt install simplescreenrecorder` |
| **Built-in** | Press `Ctrl+Alt+Shift+R` (GNOME screen record) |

Recommended: **OBS** or **SimpleScreenRecorder**, record **entire monitor** or **browser window**.

### 4. Test microphone (optional voiceover)

Speak clearly: *"Subnet Tutor — offline bilingual subnetting for ADTC 2026."*

---

## Part 2 — Record (follow timestamps)

Use `DEMO_SCRIPT.md` — rehearse once before recording.

| Time | Action | What to show |
|------|--------|--------------|
| **0:00** | Home page EN | Title: *Subnet Tutor ( Keith Barker Method )* |
| **0:05** | Voice/text | *"Offline tutor — no internet after setup"* |
| **0:15** | Click **Start Tutorial** | |
| **0:20** | **Raise Fingers** × 3 | Left hand: 2 → 4 → 8 subnets |
| **0:30** | **Explain with AI Tutor** | Wait for answer (up to 30s if LLM) |
| **0:40** | **Next** → Step 3 | Click **Fold Network** once |
| **0:45** | Click **AR** | Show Arabic RTL nav |
| **0:55** | Click **Game** | Level 1 |
| **1:05** | Enter fingers + prefix | Click **Check Answer** → success |
| **1:15** | Level 2 tab | Quick peek |
| **1:25** | Point to footer | *"LLM ready — on-device Qwen 1.5B"* |
| **1:35** | Home | *"Math & Scientific Reasoning — ADTC 2026"* |
| **1:50** | End | Fade or stop recording |

**Keep total under 2:00.**

---

## Part 3 — Upload video

### YouTube (recommended)

1. Go to https://studio.youtube.com → **Create** → **Upload video**
2. Title: `Subnet Tutor — ADTC 2026 Demo | Offline Bilingual Subnetting Tutor`
3. Visibility: **Unlisted**
4. Copy link → save for DevPost

### Or Vimeo

Upload as unlisted, copy link.

---

## Part 4 — Screenshots for DevPost

While app is running:

```bash
mkdir -p ~/Projects/subnet-tutor/screenshots
```

Capture (use Screenshot app or `gnome-screenshot -w`):

1. Home (EN)
2. Tutorial with fingers raised
3. Game level 1 or Arabic UI

Add to git (optional):

```bash
git add screenshots/
git commit -m "Add DevPost screenshots"
git push
```

---

## Part 5 — Submit on DevPost

Open **`DEVPOST_SUBMISSION.md`** — copy/paste all fields into:

https://adtc-2026.devpost.com/project/submissions/new

Required:
- GitHub: `https://github.com/mahmouddahiie-pixel/subnet-tutor`
- Video URL (from Part 3)
- Description (from DEVPOST_SUBMISSION.md)
- 2–3 screenshots

---

## Troubleshooting during recording

| Issue | Fix |
|-------|-----|
| Explain takes long | Wait — or show RAG bullet summary (still valid) |
| LLM not ready | Footer says "loading" — wait 1 min, re-record explain clip |
| Wrong language | Click EN/AR before that section |
| Over 2 min | Cut tutorial to 2 finger taps, skip Level 2 |

---

## Quick voiceover script (read while recording)

> "This is Subnet Tutor for the Africa Deep Tech Challenge 2026.
> It teaches IP subnetting using Keith Barker's finger method — fully offline.
> Students raise fingers to count powers of two, play a four-level game, and ask an on-device AI tutor.
> Here is the Arabic interface for North African classrooms.
> The model is Qwen two-point-five 1.5 billion, running on llama dot cpp on a budget laptop.
> No internet required after setup. Thank you."
