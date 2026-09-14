"""Picking new/review words and soft-matching the user's answer."""
import random


def pick_new_word(dictionary: list[dict], introduced_ids: set[str]) -> dict | None:
    candidates = [e for e in dictionary if e["id"] not in introduced_ids]
    if not candidates:
        return None
    return random.choice(candidates)


def pick_review_word(dictionary_by_id: dict[str, dict], introduced_ids: list[str]) -> dict | None:
    if not introduced_ids:
        return None
    word_id = random.choice(introduced_ids)
    return dictionary_by_id.get(word_id)


def _normalize(text: str) -> str:
    return text.strip().lower()


def is_correct(answer: str, translation: str) -> bool:
    variants = [_normalize(v) for v in translation.replace(",", ";").split(";")]
    return _normalize(answer) in variants


def record_answer(user_state: dict, word_id: str, correct: bool) -> None:
    history = user_state.setdefault("history", {})
    entry = history.setdefault(word_id, {"correct": 0, "incorrect": 0})
    entry["correct" if correct else "incorrect"] += 1
