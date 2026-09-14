"""Load the dictionary from data/dictionary.json, filtered by active languages."""
import json
from pathlib import Path


def load_dictionary(path: Path, active_languages: list[str]) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        entries = json.load(f)

    active = set(active_languages)
    return [e for e in entries if e["lang"] in active]


def index_by_id(entries: list[dict]) -> dict[str, dict]:
    return {e["id"]: e for e in entries}
