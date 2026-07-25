"""Internationalization helpers."""

from __future__ import annotations

import json
from pathlib import Path

I18N_DIR = Path(__file__).resolve().parent
_cache: dict[str, dict[str, str]] = {}


def get_strings(lang: str = "en") -> dict[str, str]:
    if lang not in _cache:
        path = I18N_DIR / f"{lang}.json"
        if not path.exists():
            path = I18N_DIR / "en.json"
        _cache[lang] = json.loads(path.read_text(encoding="utf-8"))
    return _cache[lang]


def translate(key: str, lang: str = "en") -> str:
    return get_strings(lang).get(key, key)
