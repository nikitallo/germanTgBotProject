"""Per-user state store backed by data/state.json (atomic writes)."""
import json
import tempfile
from pathlib import Path
from threading import Lock


class StateStore:
    def __init__(self, path: Path):
        self._path = path
        self._lock = Lock()
        if self._path.exists():
            with self._path.open("r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {"users": {}}

    def get_user(self, user_id: int) -> dict:
        return self._data["users"].setdefault(
            str(user_id),
            {
                "introduced_word_ids": [],
                "history": {},
                "pending_quiz": None,
                "today": None,
            },
        )

    def save(self) -> None:
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
            with open(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            Path(tmp_name).replace(self._path)
