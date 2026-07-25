# Subnet Tutor — ADTC 2026

Offline bilingual (English / Arabic) subnetting tutor for the **Africa Deep Tech Challenge 2026** Laptop LLM track.

## Features

- **Finger-counting tutorial** — interactive hands, paper-fold metaphor, guided walkthrough
- **Subnetting game** — 4 difficulty levels with deterministic grading
- **On-device AI tutor** — Qwen2.5-1.5B-Instruct via llama.cpp + lightweight local RAG (pure Python BM25)
- **100% offline** after initial model download

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Download model weights (one-time, requires internet)
bash download_model.sh

# 3. Build RAG index (automatic on first run)
python -m app.rag.indexer

# 4. Launch app
bash run.sh
# Open http://127.0.0.1:8765
```

## ADTC Submission

This repo follows the [ADTC 2026 submission template](https://github.com/Africa-Deep-Tech-Foundation/adtc-2026-submission-template):

- Domain: `math_scientific_reasoning`
- Languages: `en`, `ar`
- Model: Qwen2.5-1.5B-Instruct Q4_K_M (GGUF, llama.cpp)

### Local profiler

```bash
pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"
bash download_model.sh
adtc-profiler run --submission . --mode participant --output submission.json --skip-accuracy
```

## Project Structure

```
app/           Flask app, LLM client, RAG, game, tutorial
knowledge/     RAG corpus (EN + AR)
templates/     HTML UI
static/        CSS/JS illustrations
metadata.json  ADTC submission metadata
```

## License

GPL-3.0 (per ADTC template)
