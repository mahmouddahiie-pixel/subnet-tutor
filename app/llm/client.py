"""On-device LLM client using llama-cpp-python."""

from __future__ import annotations

import os
import re
import threading
from pathlib import Path
from typing import Optional

from app.llm.prompts import build_prompt

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = ROOT / "model" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"

_llm_instance = None
_llm_lock = threading.Lock()
_llm_loading = False
_llm_load_error: Optional[str] = None


def get_model_path() -> Path:
    env_path = os.environ.get("SUBNET_TUTOR_MODEL_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_MODEL_PATH


def is_model_available() -> bool:
    return get_model_path().is_file()


def is_model_loaded() -> bool:
    return _llm_instance is not None


def is_model_loading() -> bool:
    return _llm_loading


def get_model_load_error() -> Optional[str]:
    return _llm_load_error


def get_llm():
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    model_path = get_model_path()
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Model not found at {model_path}. Run: bash download_model.sh"
        )

    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise ImportError(
            "llama-cpp-python is not installed. Run: pip install llama-cpp-python"
        ) from exc

    n_ctx = int(os.environ.get("SUBNET_TUTOR_N_CTX", "2048"))
    n_threads = int(
        os.environ.get("SUBNET_TUTOR_N_THREADS", str(max(2, (os.cpu_count() or 4) - 1)))
    )

    with _llm_lock:
        if _llm_instance is not None:
            return _llm_instance
        _llm_instance = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            use_mmap=True,
            verbose=False,
        )
        global _llm_load_error
        _llm_load_error = None
    return _llm_instance


def preload_model() -> None:
    """Load the GGUF model in the current thread (intended for background preload)."""
    global _llm_loading, _llm_load_error

    if _llm_instance is not None or not is_model_available():
        return

    with _llm_lock:
        if _llm_instance is not None or _llm_loading:
            return
        _llm_loading = True
        _llm_load_error = None

    try:
        get_llm()
        print("[LLM] Model loaded successfully.")
    except Exception as exc:
        _llm_load_error = str(exc)
        print(f"[LLM] Failed to load model: {exc}")
    finally:
        _llm_loading = False


def retry_model_preload() -> None:
    """Clear error state and attempt preload again."""
    global _llm_load_error
    if is_model_loaded():
        return
    _llm_load_error = None
    start_model_preload()


def get_model_status_dict() -> dict:
    """Full model status for API and diagnostics."""
    path = get_model_path()
    llama_ok = False
    llama_error = None
    try:
        import llama_cpp  # noqa: F401
        llama_ok = True
    except ImportError as exc:
        llama_error = str(exc)

    if is_model_loaded():
        status = "ready"
    elif is_model_loading():
        status = "loading"
    elif _llm_load_error or llama_error:
        status = "error"
    elif not path.is_file():
        status = "unavailable"
    else:
        status = "pending"

    return {
        "available": path.is_file(),
        "loaded": is_model_loaded(),
        "loading": is_model_loading(),
        "status": status,
        "model_path": str(path),
        "model_size_mb": round(path.stat().st_size / (1024 * 1024), 1) if path.is_file() else None,
        "llama_cpp_installed": llama_ok,
        "error": _llm_load_error or llama_error,
    }


def start_model_preload() -> None:
    """Begin loading the model on a background thread so requests stay responsive."""
    if not is_model_available() or is_model_loaded() or is_model_loading():
        return
    thread = threading.Thread(target=preload_model, daemon=True, name="llm-preload")
    thread.start()


def generate_response(
    user_question: str,
    context: str,
    language: str = "en",
    max_tokens: int = 256,
) -> str:
    prompt = build_prompt(user_question, context, language)
    llm = get_llm()
    result = llm(
        prompt,
        max_tokens=max_tokens,
        temperature=0.2,
        stop=["User question:", "\n\nUser"],
    )
    text = result["choices"][0]["text"].strip()
    return text


def _clean_markdown_line(line: str) -> str:
    text = line.strip()
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def _summarize_context(context: str, language: str = "en", max_bullets: int = 5) -> list[str]:
    """Turn RAG markdown chunks into a short tutor-style bullet list."""
    bullets: list[str] = []
    sections = re.split(r"\n---\n|\n(?=## )", context)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        for line in section.splitlines():
            cleaned = _clean_markdown_line(line)
            if not cleaned or cleaned.startswith("|") or cleaned.startswith("#"):
                continue
            list_match = re.match(r"^[-*•]\s+(.+)$", cleaned) or re.match(
                r"^\d+\.\s+(.+)$", cleaned
            )
            if list_match:
                item = list_match.group(1)
                if len(item) >= 12:
                    bullets.append(item[:220])
                continue
            if "=" in cleaned and 10 <= len(cleaned) <= 180:
                bullets.append(cleaned)

        if not bullets:
            title_match = re.match(r"^#+\s*(.+)$", section.splitlines()[0].strip())
            if title_match:
                title = _clean_markdown_line(title_match.group(1))
                if title and len(title) >= 8:
                    bullets.append(title)

    deduped: list[str] = []
    seen: set[str] = set()
    for bullet in bullets:
        key = bullet.lower()[:60]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(bullet)
        if len(deduped) >= max_bullets:
            break

    if deduped:
        return deduped

    fallback = _clean_markdown_line(context.replace("\n", " "))
    if fallback:
        return [fallback[:220]]
    return (
        ["لم أجد سياقاً كافياً في المعرفة المحلية."]
        if language == "ar"
        else ["Not enough local knowledge matched your question."]
    )


def generate_fallback_response(
    user_question: str,
    context: str,
    language: str = "en",
    *,
    model_loading: bool = False,
    model_available: bool | None = None,
    model_load_error: str | None = None,
) -> str:
    """Rule-based fallback when model weights are unavailable or still loading."""
    if model_available is None:
        model_available = is_model_available()
    if model_load_error is None:
        model_load_error = get_model_load_error()

    bullets = _summarize_context(context, language)
    bullet_block = "\n".join(f"• {b}" for b in bullets)

    if language == "ar":
        if model_load_error:
            prefix = "【المعلّم الذكي】 تعذّر تحميل النموذج — إليك ملخصاً من المعرفة المحلية:\n\n"
            suffix = f"\n\nخطأ: {model_load_error[:300]}\n\nالحل: pip install llama-cpp-python ثم bash run.sh"
        elif model_loading:
            prefix = "【المعلّم الذكي】 جاري تحميل النموذج — إليك ملخصاً من المعرفة المحلية:\n\n"
            suffix = "\n\nانتظر حتى يظهر «نموذج اللغة جاهز» في الأسفل."
        elif not model_available:
            prefix = "【المعلّم الذكي】 وضع بدون نموذج — إليك ملخصاً من المعرفة المحلية:\n\n"
            suffix = "\n\nلتفعيل الشروحات الكاملة، نفّذ: bash download_model.sh"
        else:
            prefix = "【المعلّم الذكي】 إليك ملخصاً من المعرفة المحلية:\n\n"
            suffix = ""
        return f"{prefix}{bullet_block}\n\nسؤالك: {user_question}{suffix}"

    if model_load_error:
        prefix = "[AI Tutor] Model failed to load — here is a summary from local knowledge:\n\n"
        suffix = (
            f"\n\nLoad error: {model_load_error[:300]}"
            "\n\nFix: source .venv/bin/activate && pip install llama-cpp-python"
            "\nThen: bash run.sh"
            "\nDiagnose: bash scripts/diagnose_llm.sh"
        )
    elif model_loading:
        prefix = "[AI Tutor] Model is loading — here is a summary from local knowledge:\n\n"
        suffix = "\n\nWait until the footer shows «LLM ready», then try again."
    elif not model_available:
        prefix = "[AI Tutor] Offline mode — here is a summary from local knowledge:\n\n"
        suffix = "\n\nRun `bash download_model.sh` to enable full LLM explanations."
    else:
        prefix = "[AI Tutor] Here is a summary from local knowledge:\n\n"
        suffix = ""
    return f"{prefix}{bullet_block}\n\nYour question: {user_question}{suffix}"


def ask_tutor(
    user_question: str,
    context: str,
    language: str = "en",
    *,
    use_llm: bool = False,
) -> dict:
    """Answer a tutor question. Defaults to fast RAG fallback unless use_llm=True and model is ready."""
    if use_llm and is_model_loaded():
        try:
            answer = generate_response(user_question, context, language)
            return {"answer": answer, "mode": "llm"}
        except Exception as exc:
            answer = generate_fallback_response(user_question, context, language)
            return {"answer": answer, "mode": "fallback", "error": str(exc)}

    loading = is_model_loading() and not is_model_loaded()
    if is_model_loaded():
        loading = False
    answer = generate_fallback_response(
        user_question,
        context,
        language,
        model_loading=loading,
        model_available=is_model_available(),
        model_load_error=get_model_load_error(),
    )
    result: dict = {"answer": answer, "mode": "fallback"}
    if loading:
        result["model_status"] = "loading"
    elif not is_model_available():
        result["model_status"] = "unavailable"
    elif _llm_load_error:
        result["model_status"] = "error"
        result["error"] = _llm_load_error
    elif is_model_loaded():
        result["model_status"] = "ready"
    else:
        result["model_status"] = "pending"
    return result
