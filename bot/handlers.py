"""Command and message handlers, restricted to allowed users only."""
from telegram import Update
from telegram.ext import ContextTypes, filters

from bot import quiz
from bot.state import StateStore


def allowed_filter(allowed_user_ids: list[int]) -> filters.BaseFilter:
    return filters.User(user_id=allowed_user_ids)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я буду присылать тебе одно новое немецкое слово и один "
        "вопрос на повторение каждый день между 9:00 и 23:00.\n\n"
        "Команды: /help"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Раз в день — новое слово. Раз в день — вопрос по уже показанному "
        "слову: просто напиши перевод в ответ на вопрос, и я скажу, "
        "правильно это или нет."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store: StateStore = context.application.bot_data["store"]
    dictionary_by_id: dict = context.application.bot_data["dictionary_by_id"]

    user_id = update.effective_user.id
    user_state = store.get_user(user_id)
    pending = user_state.get("pending_quiz")

    if not pending:
        await update.message.reply_text("Сейчас нет активного вопроса. Дождись следующего 🙂")
        return

    word = dictionary_by_id.get(pending["word_id"])
    if word is None:
        user_state["pending_quiz"] = None
        store.save()
        await update.message.reply_text("Этот вопрос уже неактуален, дождись следующего.")
        return

    answer = update.message.text or ""
    correct = quiz.is_correct(answer, word["translation"])
    quiz.record_answer(user_state, word["id"], correct)
    user_state["pending_quiz"] = None
    store.save()

    if correct:
        await update.message.reply_text("✅ Правильно!")
    else:
        await update.message.reply_text(
            f"❌ Неправильно. Правильный перевод: {word['translation']}"
        )
