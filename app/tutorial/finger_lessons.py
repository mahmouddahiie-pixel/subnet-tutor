"""Finger-counting tutorial lesson data and helpers."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT / "knowledge"


def load_finger_table() -> list[dict]:
    path = KNOWLEDGE_DIR / "powers_of_two.json"
    return json.loads(path.read_text(encoding="utf-8"))


def get_lesson_steps(lang: str = "en") -> list[dict]:
    if lang == "ar":
        return [
            {
                "id": "intro",
                "title": "مرحباً بك في طريقة الأصابع",
                "body": "ارفع إصبعاً واحداً لكل بت تستعاره. كل إصبع يضاعف عدد الشبكات الفرعية!",
            },
            {
                "id": "powers",
                "title": "قوى العدد 2",
                "body": "عد: 2، 4، 8، 16، 32، 64، 128، 256. كل رقم = 2^عدد_الأصابع.",
            },
            {
                "id": "fold",
                "title": "تشبيه طي الورقة",
                "body": "كل طية تقسم شبكتك إلى نصفين. طية واحدة = شبكتان، طيتان = 4 شبكات.",
            },
            {
                "id": "walkthrough",
                "title": "مثال موجه",
                "body": "192.168.1.0/24 تحتاج 6 شبكات. ارفع 3 أصابع → 8 شبكات → /27",
                "example_network": "192.168.1.0/24",
                "required_subnets": 6,
                "answer_fingers": 3,
                "answer_prefix": 27,
            },
        ]
    return [
        {
            "id": "intro",
            "title": "Welcome to the Finger Method",
            "body": "Raise one finger for each bit you borrow. Each finger doubles your subnets!",
        },
        {
            "id": "powers",
            "title": "Powers of Two",
            "body": "Count: 2, 4, 8, 16, 32, 64, 128, 256. Each number = 2^fingers raised.",
        },
        {
            "id": "fold",
            "title": "Paper Fold Metaphor",
            "body": "Each fold splits your network in half. One fold = 2 subnets, two folds = 4 subnets.",
        },
        {
            "id": "walkthrough",
            "title": "Guided Walkthrough",
            "body": "192.168.1.0/24 needs 6 subnets. Raise 3 fingers → 8 subnets → /27",
            "example_network": "192.168.1.0/24",
            "required_subnets": 6,
            "answer_fingers": 3,
            "answer_prefix": 27,
        },
    ]


def validate_walkthrough(fingers: int, required_subnets: int = 6, lang: str = "en") -> dict:
    from app.i18n import translate

    table = load_finger_table()
    entry = next((row for row in table if row["finger"] == fingers), None)
    if not entry:
        return {"valid": False, "message": translate("invalid_finger_count", lang)}

    subnets = entry["subnets"]
    valid = subnets >= required_subnets

    if valid:
        message_key = "walkthrough_correct"
    elif fingers <= 0:
        message_key = "walkthrough_start"
    elif fingers <= 5:
        message_key = "walkthrough_left_progress"
    else:
        message_key = "walkthrough_right_progress"

    left_fingers = min(fingers, 5) if fingers > 0 else 0
    right_fingers = max(0, fingers - 5)

    return {
        "valid": valid,
        "subnets": subnets,
        "prefix_offset": entry["prefix_offset"],
        "block_size": entry["block_size"],
        "mask_octet": entry["mask_octet"],
        "new_prefix": 24 + entry["prefix_offset"],
        "message_key": message_key,
        "left_fingers": left_fingers,
        "right_fingers": right_fingers,
    }
