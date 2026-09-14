"""Load and validate settings.json."""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SendWindow:
    start_hour: int
    end_hour: int


@dataclass(frozen=True)
class Settings:
    bot_token: str
    allowed_user_ids: list[int]
    timezone: str
    send_window: SendWindow
    active_languages: list[str]


def load_settings(path: Path) -> Settings:
    if not path.exists():
        raise SystemExit(
            f"{path} not found. Copy settings.example.json to settings.json "
            "and fill in your own values."
        )

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    required = ["bot_token", "allowed_user_ids", "timezone", "send_window", "active_languages"]
    missing = [key for key in required if key not in raw]
    if missing:
        raise SystemExit(f"settings.json is missing fields: {', '.join(missing)}")

    if not raw["allowed_user_ids"]:
        raise SystemExit("allowed_user_ids in settings.json is empty — the bot won't respond to anyone.")

    send_window = raw["send_window"]
    return Settings(
        bot_token=raw["bot_token"],
        allowed_user_ids=[int(uid) for uid in raw["allowed_user_ids"]],
        timezone=raw["timezone"],
        send_window=SendWindow(
            start_hour=int(send_window["start_hour"]),
            end_hour=int(send_window["end_hour"]),
        ),
        active_languages=list(raw["active_languages"]),
    )
