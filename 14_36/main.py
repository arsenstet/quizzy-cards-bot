import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.exceptions import TelegramBadRequest
from text_analyzer import extract_important_words, extract_text_from_url
from keyboards import get_language_inline_keyboard, get_main_menu_inline_keyboard, get_finish_inline_keyboard
from utils import translate_word
from database import init_db, add_user, save_quiz_result, get_user_stats

# Налаштування
TOKEN = "7644901235:AAHOf3wmULThC2iVkBy2fMyUgsehPTlSCgg"
bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Зберігання стану користувача
user_state = {}
ADMIN_ID = 123456  # Заміни на свій Telegram ID


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    chat_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name
    add_user(chat_id, username)
    await message.answer(
        "👋 *Вітаю\\!* Я Quizzy Cards — твій помічник у вивченні нових слів\\.\n"
        "Обери мову тексту:",
        reply_markup=get_language_inline_keyboard(),
        parse_mode="MarkdownV2"
    )
    user_state[chat_id] = {"stage": "choose_language"}


@dp.message(Command("stats"))
async def handle_stats(message: types.Message):
    chat_id = message.chat.id
    total_words, correct_answers = get_user_stats(chat_id)
    await message.answer(
        f"*Твоя статистика:*\n"
        f"Вивчено слів: *{total_words}*\n"
        f"Правильних відповідей: *{correct_answers}*",
        parse_mode="MarkdownV2"
    )


@dp.message(Command("viewdata"))
async def handle_viewdata(message: types.Message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID:
        await message.answer("❌ *Доступ заборонено\\!*", parse_mode="MarkdownV2")
        return
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    user_text = "\\n".join([f"ID: *{u[0]}*, Username: *{u[1]}*, Created: *{u[2]}*" for u in users])
    c.execute("SELECT user_id, word, correct, timestamp FROM quiz_results")
    results = c.fetchall()
    result_text = "\\n".join([f"User ID: *{r[0]}*, Word: *{r[1]}*, Correct: *{r[2]}*, Time: *{r[3]}*" for r in results])
    await message.answer(
        f"*Користувачі:*\n{user_text or 'Пусто'}\n\n*Результати квіза:*\n{result_text or 'Пусто'}",
        parse_mode="MarkdownV2"
    )
    conn.close()


@dp.callback_query()
async def handle_callback_query(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    data = callback.data
    current_text = callback.message.text

    # Вибір мови
    if data.startswith("lang:"):
        language = data.split(":")[1]
        user_state[chat_id] = {"stage": "main_menu", "language": language}
        new_text = "✅ *Мову вибрано\\!* Що хочеш зробити?"
        try:
            if current_text != new_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=get_main_menu_inline_keyboard(),
                    parse_mode="MarkdownV2"
                )
            await callback.answer()
        except TelegramBadRequest:
            await callback.answer()

    # Головне меню: Почати квіз
    elif data == "start_quiz":
        user_state[chat_id]["stage"] = "waiting_for_text"
        new_text = "📝 *Надішли текст або посилання для аналізу:*"
        try:
            if current_text != new_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
                    ]),
                    parse_mode="MarkdownV2"
                )
            await callback.answer()
        except TelegramBadRequest:
            await callback.answer()

    # Головне меню: Переглянути статистику
    elif data == "view_stats":
        total_words, correct_answers = get_user_stats(chat_id)
        new_text = (
            f"*Твоя статистика:*\n"
            f"Вивчено слів: *{total_words}*\n"
            f"Правильних відповідей: *{correct_answers}*\n\n"
            "Що далі?"
        )
        try:
            if current_text != new_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=get_main_menu_inline_keyboard(),
                    parse_mode="MarkdownV2"
                )
            await callback.answer("📊 Статистика оновлена!")
        except TelegramBadRequest:
            await callback.answer("📊 Статистика оновлена!")

    # Головне меню: Змінити мову
    elif data == "change_language":
        user_state[chat_id]["stage"] = "choose_language"
        new_text = "🌐 *Обери мову тексту:*"
        try:
            if current_text != new_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=get_language_inline_keyboard(),
                    parse_mode="MarkdownV2"
                )
            await callback.answer()
        except TelegramBadRequest:
            await callback.answer()

    # Повернення до головного меню
    elif data == "main_menu":
        user_state[chat_id]["stage"] = "main_menu"
        new_text = "🏠 *Головне меню\\!* Що хочеш зробити?"
        try:
            if current_text != new_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=get_main_menu_inline_keyboard(),
                    parse_mode="MarkdownV2"
                )
            await callback.answer()
        except TelegramBadRequest:
            await callback.answer()

    # Після квіза: Повторити квіз
    elif data == "repeat_quiz":
        state = user_state.get(chat_id, {})
        if state.get("stage") == "finished" and "words" in state:
            state["stage"] = "quiz"
            state["current_word_index"] = 0
            state["attempts"] = 3
            state["score"] = 0
            new_text = "🔄 *Починаємо заново\\!*"
            try:
                if current_text != new_text:
                    await callback.message.edit_text(
                        new_text,
                        parse_mode="MarkdownV2"
                    )
                await send_next_word(chat_id)
            except TelegramBadRequest:
                await send_next_word(chat_id)
        else:
            new_text = "❌ *Немає квіза для повтору\\!* Повернись до головного меню\\."
            try:
                if current_text != new_text:
                    await callback.message.edit_text(
                        new_text,
                        reply_markup=get_main_menu_inline_keyboard(),
                        parse_mode="MarkdownV2"
                    )
                await callback.answer()
            except TelegramBadRequest:
                await callback.answer()
        await callback.answer()

    # Після квіза: Новий текст
    elif data == "new_text":
        user_state[chat_id]["stage"] = "waiting_for_text"
        new_text = "📝 *Надішли новий текст або посилання для аналізу:*"
        try:
            if current_text != new_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
                    ]),
                    parse_mode="MarkdownV2"
                )
            await callback.answer()
        except TelegramBadRequest:
            await callback.answer()


@dp.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id
    text = message.text

    if user_state.get(chat_id, {}).get("stage") == "waiting_for_text":
        if text.startswith("http://") or text.startswith("https://"):
            article_text = extract_text_from_url(text)
            if not article_text:
                await message.answer(
                    "❌ *Не вдалося витягти текст із посилання\\.* Спробуй ще раз\\!",
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
                    ])
                )
                return
            words = extract_important_words(article_text)
        else:
            words = extract_important_words(text)

        if words:
            if isinstance(words, dict):
                words = words[0]
            await message.answer(
                f"✨ *Я знайшов ключові слова:* _{', '.join(words)}_\\.\n"
                f"Готовий почати квіз? 🚀",
                parse_mode="MarkdownV2"
            )
            if len(words) < 5:
                await message.answer(
                    "⚠️ Знайдено мало слів\\. Можливо, текст надто короткий\\. Усе одно продовжимо\\!",
                    parse_mode="MarkdownV2"
                )
            user_state[chat_id] = {
                "stage": "quiz",
                "words": words,
                "current_word_index": 0,
                "attempts": 3,
                "score": 0,
                "total_words": len(words),
                "language": user_state.get(chat_id, {}).get("language", "en")
            }
            await send_next_word(chat_id)
        else:
            await message.answer(
                "❌ *Не вдалося знайти важливі слова\\.* Спробуй інший текст\\!",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
                ])
            )

    elif user_state.get(chat_id, {}).get("stage") == "quiz":
        await check_answer(chat_id, text)


async def send_next_word(chat_id):
    state = user_state[chat_id]
    if state["current_word_index"] < len(state["words"]):
        word = state["words"][state["current_word_index"]]
        translation = translate_word(word)
        state["current_translation"] = translation
        progress = f"*Слово {state['current_word_index'] + 1}/{state['total_words']}*"
        await bot.send_message(
            chat_id,
            f"{progress}\nПереклади слово _*{word}*_ українською:\nСпроби: *{state['attempts']}*",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
            ])
        )
    else:
        await finish_quiz(chat_id)


async def check_answer(chat_id, user_answer):
    state = user_state[chat_id]
    word = state["words"][state["current_word_index"]]
    correct_translation = state["current_translation"]

    logging.info(f"Checking answer: user_id={chat_id}, word={word}, answer={user_answer}, correct={correct_translation}")

    if user_answer.lower() == correct_translation:
        state["score"] += 1
        state["current_word_index"] += 1
        state["attempts"] = 3
        save_quiz_result(chat_id, word, 1)
        await bot.send_message(
            chat_id,
            "✅ *Правильно\\!* Переходимо до наступного слова\\! 🎉",
            parse_mode="MarkdownV2"
        )
        await send_next_word(chat_id)
    else:
        state["attempts"] -= 1
        if state["attempts"] > 0:
            await bot.send_message(
                chat_id,
                f"❌ *Неправильно\\.* Спроби: *{state['attempts']}*\\. Спробуй ще раз\\!",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
                ])
            )
        else:
            state["current_word_index"] += 1
            state["attempts"] = 3
            save_quiz_result(chat_id, word, 0)
            await bot.send_message(
                chat_id,
                f"⏳ *Спроби закінчились\\!* Правильний переклад: _*{correct_translation}*_\\.\n"
                "Йдемо далі\\!",
                parse_mode="MarkdownV2"
            )
            await send_next_word(chat_id)


async def finish_quiz(chat_id):
    state = user_state[chat_id]
    score = state["score"]
    total = state["total_words"]
    await bot.send_message(
        chat_id,
        f"🏁 *Квіз завершено\\!*\nТвій результат: *{score}/{total}* 🎉\n"
        "Що хочеш зробити далі?",
        reply_markup=get_finish_inline_keyboard(),
        parse_mode="MarkdownV2"
    )
    state["stage"] = "finished"


async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())