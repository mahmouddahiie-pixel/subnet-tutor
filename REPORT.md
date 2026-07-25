# Subnet Tutor — Technical Report (ADTC 2026)

## 1. Problem Definition

**Problem:** Students and beginners struggle to understand IP subnetting — especially the math behind powers of two, borrowed bits, and CIDR prefix calculation. In many African classrooms and training centers, internet access is unreliable, making cloud-based AI tutors unusable.

**Target users:** Children and beginners learning basic networking; IT students in offline or low-connectivity environments; Arabic and English speakers.

**Solution:** Subnet Tutor is an offline desktop web application that combines:
1. An interactive **finger-counting tutorial** (visual subnetting method)
2. A **4-level subnetting game** with deterministic grading
3. An **on-device LLM** (Qwen2.5-1.5B-Instruct, GGUF Q4_K_M) with **local RAG** for math/scientific reasoning explanations

## 2. Constraints

| Constraint | How we address it |
|---|---|
| 8 GB RAM / ~7 GB peak | Q4_K_M 1.5B model (~1.2 GB); lazy LLM load; small embedding model |
| Zero internet at runtime | All assets bundled; model via `download_model.sh` pre-fetch only |
| llama.cpp only | `llama-cpp-python` wrapper; GGUF weights |
| Math & Scientific Reasoning domain | Powers of 2, log₂, CIDR calculations, step-by-step proofs |
| Bilingual EN/AR | UI i18n JSON, RTL layout, Arabic RAG corpus |

## 3. Design Decisions

### Model: Qwen2.5-1.5B-Instruct Q4_K_M

- **Why:** Strong multilingual support (including Arabic), good instruction-following, fits comfortably in RAM budget on ADTC Standard Laptop.
- **Alternatives considered:** Phi-3-mini (larger RAM footprint), SmolLM2-1.7B (weaker Arabic).

### RAG over fine-tuning

- **Why:** Faster iteration before deadline; subnetting rules are structured and fit a local knowledge base well; no GPU training required.
- **Corpus:** `finger_method_en.md`, `finger_method_ar.md`, `powers_of_two.json`, `worked_problems.json`, `glossary_en_ar.json`
- **Embeddings:** lightweight BM25 keyword search (pure Python — no PyTorch, ~0 extra disk)
- **Vector store:** in-memory document index built from local `knowledge/` files

### Deterministic grading

The LLM **explains** but does **not grade**. Answer checking uses Python `ipaddress` module to avoid hallucinated scores.

### Application stack

- **Python 3.11+ / Flask** — local web UI at `127.0.0.1:8765`
- **SVG/Canvas** — finger hands, network fold animation
- **Session-based progress** — score, streak, badges (no account needed)

## 4. Architecture

```
User → Flask UI → Game/Tutorial modules
              ↓
         RAG retriever (ChromaDB + multilingual embeddings)
              ↓
         llama.cpp (Qwen2.5-1.5B Q4_K_M) → explanation
```

**Fallback mode:** If model weights are not downloaded, the app serves RAG context in a structured fallback response so the UI remains functional offline.

## 5. African Use Case

Subnet Tutor targets **offline IT education in African schools** where:
- Cloud LLM APIs are unaffordable or unreachable
- Commodity 8 GB laptops are the primary device
- Arabic-speaking regions (North Africa) and English-speaking regions both need networking skills

This aligns with the ADTC mission: useful on-device AI on hardware Africans already own.

## 6. Performance Benchmarks

Run on ADTC Standard Laptop (Ubuntu 22.04, 8 GB RAM, integrated GPU):

```bash
pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"
bash download_model.sh
adtc-profiler run --submission . --mode participant --output submission.json --skip-accuracy
```

**Measured results** *(fill in after `bash run_profiler.sh` on 8 GB laptop)*:

| Metric | Target | Measured | Pass? |
|---|---|---|---|
| Peak RAM | ≤ 4 GB | ___ MB | |
| Throughput (TPS) | ≥ 10 tok/s | ___ | |
| Thermal throttle | None > 85°C | ___ | |
| Profiler mode | participant | ___ | |

```json
// Paste key fields from submission.json:
// "peak_ram_mb": ...,
// "tokens_per_second": ...,
// "measured_on": "participant_laptop"
```

## 7. Test Prompts (metadata.json)

1. **tp_001:** School network 192.168.5.0/24, 25 usable hosts — find mask, subnets, block size using powers of 2.
2. **tp_002:** Arabic explanation of why borrowing 3 bits from /24 creates 8 subnets using finger method.

## 8. Tools Used

- llama.cpp / llama-cpp-python
- Qwen2.5-1.5B-Instruct GGUF (Hugging Face)
- sentence-transformers, ChromaDB (removed — replaced with pure-Python BM25 to save disk)
- Flask, Python ipaddress
- ADTC profiler (benchmarking)

## 9. Screenshots / Demo

Launch: `bash run.sh` → http://127.0.0.1:8765

- **Home:** Overview with network illustration
- **Tutorial:** Interactive finger counting + paper fold + AI Explain
- **Game:** 4 levels with scoring and badges

*Add screenshots and 2-minute demo video before final submission.*
