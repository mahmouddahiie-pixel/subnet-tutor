# Easy Install Guide — Subnet Tutor

Works on **Ubuntu 22.04+** with **8 GB RAM** (ADTC target). App still runs on smaller machines using local-knowledge fallback if the LLM cannot load.

---

## One command (recommended)

```bash
git clone https://github.com/mahmouddahiie-pixel/subnet-tutor.git
cd subnet-tutor
bash install.sh
bash run.sh
```

Open **http://127.0.0.1:8765**

---

## What `install.sh` does

1. Creates Python virtual environment (`.venv`)
2. Installs Flask + llama-cpp-python
3. Builds offline knowledge index
4. Downloads Qwen2.5-1.5B GGUF model (~1.1 GB, **internet required once**)

---

## After starting (`bash run.sh`)

| Footer message | Meaning |
|----------------|---------|
| **Loading model...** | Wait 1–2 minutes (first run) |
| **LLM ready** | Full AI tutor works |
| **Tutor fallback mode** | Model missing — run `bash download_model.sh` |
| **LLM load failed** | Run `bash scripts/diagnose_llm.sh` |

### Explain / Hint buttons

- **Before LLM ready:** Shows bullet summary from local knowledge (instant)
- **After LLM ready:** Full AI explanation (may take 30–90 seconds on slow CPUs)
- If AI is slow, you still get a local summary — never stuck on "Thinking..."

---

## Test machine checklist

```bash
cd subnet-tutor
bash scripts/diagnose_llm.sh   # Must pass before demo
bash run.sh
```

In browser:
1. Hard refresh: **Ctrl+Shift+R**
2. Wait for footer: **LLM ready**
3. Tutorial → **Explain with AI Tutor**
4. Game → **Get Hint**

---

## Minimum requirements

| Component | Required |
|-----------|----------|
| OS | Ubuntu 22.04+ (64-bit) |
| RAM | 4 GB minimum, **8 GB recommended** |
| Disk | ~2 GB free (model + venv) |
| Python | 3.10–3.12 recommended (3.14 may work) |
| Internet | Once for `install.sh` only |

---

## Troubleshooting

### Model won't load (test machine)

```bash
source .venv/bin/activate
pip install llama-cpp-python
bash scripts/diagnose_llm.sh
```

Low RAM? Set fewer threads:

```bash
export SUBNET_TUTOR_N_THREADS=2
bash run.sh
```

### "Request timed out"

Hard refresh (**Ctrl+Shift+R**) to load latest JS (`?v=5`).

Hints and Explain use **15s** for local knowledge, **3 min** for full LLM.

### App works without LLM

Tutorial, game, and grading work **offline without the model**. Only AI Explain/Hint need the LLM for full answers — fallback bullets always work.

---

## ADTC profiler (optional)

```bash
sudo apt install llama.cpp-tools
bash run_profiler.sh
```

---

## Quick validation

```bash
.venv/bin/python -m unittest discover tests -v
bash validate_submission.sh
```
