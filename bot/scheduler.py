"""Daily random schedule for the new-word and review-quiz sends.

For each allowed user, two random times are picked independently within
settings.send_window for the current day (in settings.timezone). If the bot
restarts after a picked time has already passed, today's send isn't skipped —
it's rescheduled a few minutes out instead.
"""
import logging
import random
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from telegram.ext import Application, ContextTypes

from bot import quiz
from bot.config import Settings
from bot.state import StateStore

logger = logging.getLogger(__name__)

MIN_CATCHUP_DELAY_SECONDS = 60
MAX_CATCHUP_DELAY_SECONDS = 300


def _random_time_today(now: datetime, start_hour: int, end_hour: int) -> datetime:
    window_start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    span_seconds = max((end_hour - start_hour) * 3600 - 1, 0)
    return window_start + timedelta(seconds=random.randint(0, span_seconds))


def _ensure_today_schedule(user_state: dict, now: datetime, settings: Settings) -> dict:
    today_str = now.date().isoformat()
    today = user_state.get("today")
    if today and today.get("date") == today_str:
        return today

    today = {
        "date": today_str,
        "new_word_time": _random_time_today(
            now, settings.send_window.start_hour, settings.send_window.end_hour
        ).isoformat(),
        "quiz_time": _random_time_today(
            now, settings.send_window.start_hour, settings.send_window.end_hour
        ).isoformat(),
        "new_word_sent": False,
        "quiz_sent": False,
    }
    user_state["today"] = today
    return today


def _schedule_once(job_queue, run_at: datetime, now: datetime, callback, user_id: int, name: str) -> None:
    if run_at <= now:
        run_at = now + timedelta(
            seconds=random.randint(MIN_CATCHUP_DELAY_SECONDS, MAX_CATCHUP_DELAY_SECONDS)
        )
    for job in job_queue.get_jobs_by_name(name):
        job.schedule_removal()
    job_queue.run_once(callback, when=run_at, user_id=user_id, name=name)


def schedule_all_users(application: Application) -> None:
    settings: Settings = application.bot_data["settings"]
    tz: ZoneInfo = application.bot_data["tz"]
    store: StateStore = application.bot_data["store"]
    now = datetime.now(tz)

    for user_id in settings.allowed_user_ids:
        user_state = store.get_user(user_id)
        today = _ensure_today_schedule(user_state, now, settings)

        if not today["new_word_sent"]:
            _schedule_once(
                application.job_queue,
                datetime.fromisoformat(today["new_word_time"]),
                now,
                send_new_word,
                user_id,
                f"new_word_{user_id}",
            )
        if not today["quiz_sent"]:
            _schedule_once(
                application.job_queue,
                datetime.fromisoformat(today["quiz_time"]),
                now,
                send_review_quiz,
                user_id,
                f"quiz_{user_id}",
            )

    store.save()


async def daily_reschedule(context: ContextTypes.DEFAULT_TYPE) -> None:
    schedule_all_users(context.application)


async def send_new_word(context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = context.job.user_id
    store: StateStore = context.application.bot_data["store"]
    dictionary: list[dict] = context.application.bot_data["dictionary"]

    user_state = store.get_user(user_id)
    introduced = set(user_state["introduced_word_ids"])
    word = quiz.pick_new_word(dictionary, introduced)

    if word is None:
        text = "🎉 Ты уже выучил все слова из словаря! Новых пока нет."
    else:
        user_state["introduced_word_ids"].append(word["id"])
        text = f"📚 Новое слово дня:\n\n{word['term']} — {word['translation']}"

    user_state["today"]["new_word_sent"] = True
    store.save()

    await context.bot.send_message(chat_id=user_id, text=text)


async def send_review_quiz(context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = context.job.user_id
    store: StateStore = context.application.bot_data["store"]
    dictionary_by_id: dict[str, dict] = context.application.bot_data["dictionary_by_id"]

    user_state = store.get_user(user_id)
    word = quiz.pick_review_word(dictionary_by_id, user_state["introduced_word_ids"])

    if word is None:
        text = "Пока нечего повторять — дождись первого нового слова 🙂"
    else:
        tz: ZoneInfo = context.application.bot_data["tz"]
        user_state["pending_quiz"] = {
            "word_id": word["id"],
            "asked_at": datetime.now(tz).isoformat(),
        }
        text = f"🔁 Как переводится:\n\n{word['term']}"

    user_state["today"]["quiz_sent"] = True
    store.save()

    await context.bot.send_message(chat_id=user_id, text=text)
