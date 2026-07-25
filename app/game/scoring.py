"""Game scoring and progress tracking."""

from __future__ import annotations

BADGES = {
    "first_correct": {"en": "First Success", "ar": "أول نجاح"},
    "finger_master": {"en": "Finger Master", "ar": "سيد الأصابع"},
    "subnet_scholar": {"en": "Subnet Scholar", "ar": "عالم الشبكات"},
    "network_ninja": {"en": "Network Ninja", "ar": "محترف الشبكات"},
}


def update_score(state: dict, level: int, correct: bool) -> dict:
    state.setdefault("score", 0)
    state.setdefault("streak", 0)
    state.setdefault("badges", [])
    state.setdefault("levels_completed", {str(i): 0 for i in range(1, 5)})

    if correct:
        points = {1: 10, 2: 20, 3: 30, 4: 40}.get(level, 10)
        state["score"] += points + state["streak"] * 2
        state["streak"] += 1
        state["levels_completed"][str(level)] = state["levels_completed"].get(str(level), 0) + 1
        _award_badges(state, level)
    else:
        state["streak"] = 0

    return state


def _award_badges(state: dict, level: int) -> None:
    badges = state["badges"]
    total_correct = sum(state["levels_completed"].values())

    if total_correct >= 1 and "first_correct" not in badges:
        badges.append("first_correct")
    if state["levels_completed"].get("1", 0) >= 3 and "finger_master" not in badges:
        badges.append("finger_master")
    if state["levels_completed"].get("2", 0) >= 3 and "subnet_scholar" not in badges:
        badges.append("subnet_scholar")
    if level == 4 and "network_ninja" not in badges:
        badges.append("network_ninja")


def badge_labels(badge_ids: list[str], lang: str = "en") -> list[str]:
    return [BADGES[b][lang] for b in badge_ids if b in BADGES]
