# DevPost Submission — Copy & Paste Guide

**Challenge:** [ADTC 2026](https://adtc-2026.devpost.com)  
**Submit at:** https://adtc-2026.devpost.com/project/submissions/new  
**Deadline:** August 24, 2026 @ 11:45pm PDT

---

## Before you submit

- [ ] Demo video recorded and uploaded (YouTube unlisted or Vimeo)
- [ ] GitHub repo public: https://github.com/mahmouddahiie-pixel/subnet-tutor
- [ ] `metadata.json` filled in ✓
- [ ] `REPORT.md` includes profiler numbers ✓
- [ ] `download_model.sh` works on fresh clone

---

## Project title

```
Subnet Tutor — Offline Bilingual Subnetting Tutor (Keith Barker Method)
```

---

## Elevator pitch (short description)

```
An offline, on-device subnetting tutor for ADTC 2026. Teaches IP subnetting through Keith Barker's finger-counting method with interactive hands, a 4-level game, and a local Qwen2.5-1.5B LLM tutor — fully bilingual (English + Arabic). Runs on an 8 GB laptop with no internet after setup.
```

---

## Full description

```markdown
## Problem

Students struggle with IP subnetting math (powers of 2, CIDR, borrowed bits). In many African classrooms, cloud AI tutors are unavailable due to cost and unreliable internet.

## Solution

**Subnet Tutor** is an end-to-end offline application combining:

1. **Interactive tutorial** — Keith Barker finger-counting method with SVG hands, paper-fold metaphor, and guided walkthrough
2. **4-level subnetting game** — progressive difficulty with deterministic grading (Python `ipaddress`)
3. **On-device AI tutor** — Qwen2.5-1.5B-Instruct (GGUF Q4_K_M) via llama.cpp + local RAG knowledge base
4. **Bilingual UI** — full English and Arabic support with RTL layout

## ADTC alignment

| Criterion | How we address it |
|-----------|-------------------|
| Domain | Math & Scientific Reasoning — powers of 2, log₂, CIDR calculations |
| Offline | 100% on-device after `download_model.sh`; zero runtime network calls |
| Hardware | Q4_K_M 1.5B model; peak RSS ~1655 MB in profiler run |
| African use case | Offline bilingual IT education for under-connected schools |
| llama.cpp | Mandatory GGUF runtime via llama-cpp-python |

## Benchmark highlights (participant laptop)

- Peak RSS: **1655 MB**
- Generation TPS: **7.36 tok/s**
- Thermal throttle: **None**
- Model: Qwen2.5-1.5B-Instruct Q4_K_M

## Try it

```bash
git clone https://github.com/mahmouddahiie-pixel/subnet-tutor.git
cd subnet-tutor
bash setup.sh
bash download_model.sh
bash run.sh
# → http://127.0.0.1:8765
```

## Team

Mahmoud Dahy — mahmouddahiie@gmail.com
```

---

## Links to attach

| Field | URL |
|-------|-----|
| **GitHub repository** | https://github.com/mahmouddahiie-pixel/subnet-tutor |
| **Demo video** | *(paste your YouTube/Vimeo link after recording)* |
| **Optional: live demo** | http://127.0.0.1:8765 (local only — mention in video) |

---

## Built with / Technologies

```
Python, Flask, llama.cpp, llama-cpp-python, Qwen2.5-1.5B-Instruct, GGUF Q4_K_M, HTML/CSS/JavaScript, Python ipaddress, ADTC profiler
```

---

## Domain (select on DevPost)

```
Math & Scientific Reasoning
```

---

## African Use Case Bonus

Check **yes** if asked — offline bilingual subnetting education for African schools without reliable internet.

---

## Video upload checklist

**Automated demo already generated:**

```bash
bash automate_submission.sh
# → demo_output/subnet-tutor-demo.mp4 (~20s)
# → screenshots/*.png
```

### Option A — YouTube (recommended by DevPost)

1. Upload `demo_output/subnet-tutor-demo.mp4` to YouTube Studio → **Unlisted**
2. Title: `Subnet Tutor — ADTC 2026 Demo`
3. Paste link below into DevPost

### Option B — GitHub Release (automated)

```bash
bash upload_demo_release.sh
# Copy the release MP4 URL into DevPost video field
```

---

## Final submit steps

1. Go to https://adtc-2026.devpost.com
2. Click **Submit Project** (must be logged in / registered)
3. Fill all fields using text above
4. Attach GitHub URL + video URL
5. Upload 2–3 screenshots (home, tutorial, game)
6. Review and **Submit**

---

## Screenshots to capture

Save as PNG in `screenshots/` folder, upload to DevPost:

1. `home-en.png` — Home page English
2. `tutorial-fingers.png` — Finger counting with hands raised
3. `game-ar.png` — Game in Arabic (optional fourth: explain tutor answer)

```bash
# Start app, then use Screenshot tool (PrtScn) or:
gnome-screenshot -w -f screenshots/home-en.png
```
