"""Command and message handlers, restricted to allowed users only."""
from telegram import Update
from telegram.ext import ContextTypes, filters

from bot import quiz
from bot.scheduler import build_new_word_reply, build_review_quiz_reply
from bot.state import StateStore


def allowed_filter(allowed_user_ids: list[int]) -> filters.BaseFilter:
    return filters.User(user_id=allowed_user_ids)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я буду присылать тебе одно новое немецкое слово и один "
        "вопрос на повторение каждый день между 9:00 и 23:00.\n\n"
        "Команды:\n"
        "/word — получить новое слово прямо сейчас\n"
        "/check — пройти тест прямо сейчас\n"
        "/stat — статистика по словам\n"
        "/help — подробнее о том, как это работает"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Раз в день — новое слово. Раз в день — вопрос по уже показанному "
        "слову: просто напиши перевод в ответ на вопрос, и я скажу, "
        "правильно это или нет.\n\n"
        "Команды:\n"
        "/word — получить новое слово прямо сейчас (тоже пойдёт в число изученных)\n"
        "/check — пройти тест прямо сейчас по одному из уже изученных слов\n"
        "/stat — сколько слов уже отправлено и сколько осталось\n"
        "/help — эта справка"
    )


async def word_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store: StateStore = context.application.bot_data["store"]
    user_id = update.effective_user.id

    text = build_new_word_reply(context.application, user_id)
    store.save()

    await update.message.reply_text(text)


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store: StateStore = context.application.bot_data["store"]
    user_id = update.effective_user.id

    text = build_review_quiz_reply(context.application, user_id)
    store.save()

    await update.message.reply_text(text)


async def stat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store: StateStore = context.application.bot_data["store"]
    dictionary: list[dict] = context.application.bot_data["dictionary"]

    user_id = update.effective_user.id
    user_state = store.get_user(user_id)

    sent = len(user_state["introduced_word_ids"])
    total = len(dictionary)
    remaining = max(total - sent, 0)

    correct = sum(entry["correct"] for entry in user_state["history"].values())
    incorrect = sum(entry["incorrect"] for entry in user_state["history"].values())

    lines = [
        "📊 Статистика:",
        f"Отправлено слов: {sent} из {total}",
        f"Осталось новых: {remaining}",
    ]
    if correct or incorrect:
        lines.append(f"Ответов в тестах: {correct + incorrect} (✅ {correct} / ❌ {incorrect})")

    await update.message.reply_text("\n".join(lines))


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
