"""Lightweight local RAG — pure Python, no PyTorch/ChromaDB."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT / "knowledge"

_documents: list[dict] | None = None


def _chunk_markdown(text: str, source: str, lang: str) -> list[dict]:
    chunks: list[dict] = []
    sections = re.split(r"\n(?=## )", text)
    for section in sections:
        section = section.strip()
        if not section:
            continue
        title_match = re.match(r"^#\s*(.+)", section)
        title = title_match.group(1).strip() if title_match else source
        chunks.append(
            {
                "id": f"{source}_{len(chunks)}",
                "text": section,
                "metadata": {"source": source, "lang": lang, "title": title},
            }
        )
    return chunks


def load_documents() -> list[dict]:
    documents: list[dict] = []

    for md_file, lang in [
        ("finger_method_en.md", "en"),
        ("finger_method_ar.md", "ar"),
    ]:
        path = KNOWLEDGE_DIR / md_file
        if path.exists():
            documents.extend(
                _chunk_markdown(path.read_text(encoding="utf-8"), md_file, lang)
            )

    powers_path = KNOWLEDGE_DIR / "powers_of_two.json"
    if powers_path.exists():
        table = json.loads(powers_path.read_text(encoding="utf-8"))
        documents.append(
            {
                "id": "powers_of_two",
                "text": "Finger powers of two table:\n" + json.dumps(table, indent=2),
                "metadata": {
                    "source": "powers_of_two.json",
                    "lang": "en",
                    "title": "Powers of Two Table",
                },
            }
        )

    problems_path = KNOWLEDGE_DIR / "worked_problems.json"
    if problems_path.exists():
        for problem in json.loads(problems_path.read_text(encoding="utf-8")):
            documents.append(
                {
                    "id": problem["id"],
                    "text": json.dumps(problem, ensure_ascii=False, indent=2),
                    "metadata": {
                        "source": "worked_problems.json",
                        "lang": problem.get("lang", "en"),
                        "title": f"Worked problem {problem['id']}",
                    },
                }
            )

    glossary_path = KNOWLEDGE_DIR / "glossary_en_ar.json"
    if glossary_path.exists():
        glossary = json.loads(glossary_path.read_text(encoding="utf-8"))
        documents.append(
            {
                "id": "glossary",
                "text": "Networking glossary EN/AR:\n"
                + json.dumps(glossary, ensure_ascii=False, indent=2),
                "metadata": {
                    "source": "glossary_en_ar.json",
                    "lang": "both",
                    "title": "Glossary",
                },
            }
        )

    return documents


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w\u0600-\u06FF]+", text.lower())


def _get_documents() -> list[dict]:
    global _documents
    if _documents is None:
        _documents = load_documents()
    return _documents


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    avg_dl: float,
    doc_freq: Counter,
    n_docs: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not doc_tokens:
        return 0.0
    dl = len(doc_tokens)
    tf = Counter(doc_tokens)
    score = 0.0
    for term in query_tokens:
        if term not in tf:
            continue
        df = doc_freq.get(term, 0)
        idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
        freq = tf[term]
        denom = freq + k1 * (1 - b + b * dl / avg_dl)
        score += idf * (freq * (k1 + 1)) / denom
    return score


def build_index(force: bool = False) -> int:
    global _documents
    if force or _documents is None:
        _documents = load_documents()
    return len(_documents)


def retrieve(query: str, language: Optional[str] = None, top_k: int = 3) -> str:
    docs = _get_documents()
    if not docs:
        return "No relevant context found."

    if language in ("en", "ar"):
        filtered = [
            d
            for d in docs
            if d["metadata"].get("lang") in (language, "both")
        ]
        if filtered:
            docs = filtered

    query_tokens = _tokenize(query)
    if not query_tokens:
        return docs[0]["text"]

    tokenized = [_tokenize(d["text"]) for d in docs]
    avg_dl = sum(len(t) for t in tokenized) / len(tokenized)
    doc_freq: Counter = Counter()
    for tokens in tokenized:
        for term in set(tokens):
            doc_freq[term] += 1

    scored = [
        (_bm25_score(query_tokens, tokens, avg_dl, doc_freq, len(docs)), doc)
        for doc, tokens in zip(docs, tokenized)
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [doc["text"] for score, doc in scored[:top_k] if score > 0]

    if not top:
        top = [doc["text"] for doc in docs[:top_k]]

    return "\n\n---\n\n".join(top)
