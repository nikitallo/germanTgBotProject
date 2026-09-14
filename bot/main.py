"""Entry point: builds the Application and wires up handlers and the scheduler."""
import logging
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.config import load_settings
from bot.dictionary import index_by_id, load_dictionary
from bot.handlers import allowed_filter, handle_text, help_command, start_command
from bot.scheduler import daily_reschedule, schedule_all_users
from bot.state import StateStore

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_PATH = BASE_DIR / "settings.json"
DICTIONARY_PATH = BASE_DIR / "data" / "dictionary.json"
STATE_PATH = BASE_DIR / "data" / "state.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    schedule_all_users(application)


def main() -> None:
    settings = load_settings(SETTINGS_PATH)
    tz = ZoneInfo(settings.timezone)

    dictionary = load_dictionary(DICTIONARY_PATH, settings.active_languages)
    if not dictionary:
        logger.warning(
            "Dictionary is empty for languages %s — run scripts/import_dictionary.py",
            settings.active_languages,
        )

    application = (
        Application.builder()
        .token(settings.bot_token)
        .post_init(post_init)
        .build()
    )
    application.bot_data.update(
        {
            "settings": settings,
            "tz": tz,
            "dictionary": dictionary,
            "dictionary_by_id": index_by_id(dictionary),
            "store": StateStore(STATE_PATH),
        }
    )

    allowed = allowed_filter(settings.allowed_user_ids)
    application.add_handler(CommandHandler("start", start_command, filters=allowed))
    application.add_handler(CommandHandler("help", help_command, filters=allowed))
    application.add_handler(
        MessageHandler(allowed & filters.TEXT & ~filters.COMMAND, handle_text)
    )

    application.job_queue.run_daily(
        daily_reschedule,
        time=time(hour=0, minute=5, tzinfo=tz),
        name="daily_reschedule",
    )

    logger.info("Starting bot for users: %s", settings.allowed_user_ids)
    application.run_polling()


if __name__ == "__main__":
    main()
