# ADTC 2026 — Final Submission Guide

Complete these steps in order before DevPost upload.

---

## Step 1 — Update `metadata.json`

Replace placeholders with your registered ADTC team info:

```json
"team_id": "YOUR-TEAM-ID",
"submitter": {
  "name": "Your Full Name",
  "email": "your-email@domain.com",
  "github_handle": "your-github-username"
}
```

**Send your details to the agent or edit the file directly.**

---

## Step 2 — Install Git & push public repo

```bash
sudo apt install git gh

cd ~/Projects/subnet-tutor
git init
git add .
git status   # confirm model/*.gguf is NOT listed
git commit -m "Subnet Tutor — ADTC 2026 submission"

# Create repo on GitHub (public), then:
git remote add origin https://github.com/mahmouddahiie-pixel/subnet-tutor.git
git branch -M main
git push -u origin main
```

`.gitignore` already excludes `model/`, `*.gguf`, `.venv/`.

---

## Step 3 — Run ADTC profiler

On your **8 GB Ubuntu 22.04** laptop:

```bash
cd ~/Projects/subnet-tutor
source .venv/bin/activate
sudo apt install git   # required for profiler install
pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"

# Install llama.cpp llama-bench if not on PATH
bash download_model.sh
bash run_profiler.sh
```

Copy numbers from `submission.json` into `REPORT.md` Section 6.

---

## Step 4 — Update REPORT.md

Add actual benchmark results:

- Peak RAM (MB)
- Tokens per second (TPS)
- Measured on: participant_laptop / audit

---

## Step 5 — Record demo video

Follow **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** — ≤2 min, EN + AR, tutorial + game + explain.

---

## Step 6 — Browser smoke test

```bash
bash run.sh
# Hard refresh Ctrl+Shift+R
```

Checklist:
- [ ] Home loads
- [ ] Tutorial: fingers, explain, fold
- [ ] Game levels 1–4
- [ ] EN ↔ AR switch
- [ ] Footer shows LLM ready after ~1 min

---

## Step 7 — DevPost submission

Submit at: https://adtc-2026.devpost.com

Include:
- Public GitHub repo URL
- REPORT.md content / PDF
- Demo video link
- Screenshots (home, tutorial, game)

---

## Quick validation

```bash
bash validate_submission.sh
.venv/bin/python -m unittest discover tests -v
```

Expected: **81/81 tests pass**
