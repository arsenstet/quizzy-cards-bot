import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.exceptions import TelegramBadRequest
from flask import Flask, request
from text_analyzer import extract_important_words, extract_text_from_url
from keyboards import get_language_inline_keyboard, get_main_menu_inline_keyboard, get_finish_inline_keyboard, get_back_and_main_menu_keyboard
from utils import translate_word
from database import init_db, add_user, save_quiz_result, get_user_stats, view_all_data
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()

# Налаштування
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Зберігання стану користувача
user_state = {}
ADMIN_ID = 123456  # Заміни на свій Telegram ID

# Визначення, чи запуск локальний
IS_LOCAL = os.getenv("IS_LOCAL", "true").lower() == "true"


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    chat_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name
    add_user(chat_id, username)
    await message.answer(
        "👋 *Вітаю\\!* Я *Quizzy Cards* — твій помічник у вивченні нових слів\\.\n"
        "📚 Надсилай текст або посилання, а я створю квіз із ключовими словами\\.\n"
        "📊 Переглядай статистику своїх відповідей\\!\n\n"
        "*Обери мову, щоб почати:*",
        parse_mode="MarkdownV2"
    )
    await message.answer(
        "📍 *Вибір мови*\n"
        "Обери мову тексту для квіза\\.",
        reply_markup=get_language_inline_keyboard(),
        parse_mode="MarkdownV2"
    )
    user_state[chat_id] = {"stage": "choose_language"}


@dp.message(Command("stats"))
async def handle_stats(message: types.Message):
    chat_id = message.chat.id
    total_words, correct_answers = get_user_stats(chat_id)
    await message.answer(
        f"📍 *Статистика*\n"
        f"*Твій прогрес:*\n"
        f"• Вивчено слів: *{total_words}*\n"
        f"• Правильних відповідей: *{correct_answers}*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
        ]),
        parse_mode="MarkdownV2"
    )


@dp.message(Command("viewdata"))
async def handle_viewdata(message: types.Message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID:
        await message.answer("❌ *Доступ заборонено\\!*", parse_mode="MarkdownV2")
        return
    users, results = view_all_data()
    user_text = "\\n".join([f"ID: *{u[0]}*, Username: *{u[1]}*, Created: *{u[2]}*" for u in users])
    result_text = "\\n".join([f"User ID: *{r[0]}*, Word: *{r[1]}*, Correct: *{r[2]}*, Time: *{r[3]}*" for r in results])
    await message.answer(
        f"*Користувачі:*\n{user_text or 'Пусто'}\n\n*Результати квіза:*\n{result_text or 'Пусто'}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
        ]),
        parse_mode="MarkdownV2"
    )


@dp.callback_query()
async def handle_callback_query(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    data = callback.data
    current_text = callback.message.text
    logging.info(f"Callback received: chat_id={chat_id}, data={data}")

    if data.startswith("lang:"):
        language = data.split(":")[1]
        user_state[chat_id] = {"stage": "main_menu", "language": language}
        new_text = (
            "📍 *Головне меню*\n"
            "✅ *Мову вибрано\\!*\n"
            "• 📝 *Почати квіз* — створюй картки зі слів\n"
            "• 📊 *Статистика* — твій прогрес\n"
            "• 🌐 *Змінити мову* — вибери іншу мову"
        )
        try:
            if current_text != new_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=get_main_menu_inline_keyboard(),
                    parse_mode="MarkdownV2"
                )
            await callback.answer()
        except TelegramBadRequest as e:
            logging.error(f"Failed to edit message: {e}")
            await callback.answer()

    elif data == "start_quiz":
        user_state[chat_id]["stage"] = "waiting_for_text"
        new_text = (
            "📍 *Введення тексту*\n"
            "📝 *Надішли текст або посилання для аналізу:*"
        )
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
        except TelegramBadRequest as e:
            logging.error(f"Failed to edit message: {e}")
            await callback.answer()

    elif data == "view_stats":
        total_words, correct_answers = get_user_stats(chat_id)
        new_text = (
            "📍 *Статистика*\n"
            f"*Твій прогрес:*\n"
            f"• Вивчено слів: *{total_words}*\n"
            f"• Правильних відповідей: *{correct_answers}*"
        )
        try:
            if current_text != new_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
                    ]),
                    parse_mode="MarkdownV2"
                )
            await callback.answer("📊 Статистика оновлена!")
        except TelegramBadRequest as e:
            logging.error(f"Failed to edit message: {e}")
            await callback.answer("📊 Статистика оновлена!")

    elif data == "change_language":
        user_state[chat_id]["stage"] = "choose_language"
        new_text = (
            "📍 *Вибір мови*\n"
            "🌐 *Обери мову тексту:*"
        )
        try:
            if current_text != new_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=get_language_inline_keyboard(),
                    parse_mode="MarkdownV2"
                )
            await callback.answer()
        except TelegramBadRequest as e:
            logging.error(f"Failed to edit message: {e}")
            await callback.answer()

    elif data == "main_menu":
        user_state[chat_id]["stage"] = "main_menu"
        new_text = (
            "📍 *Головне меню*\n"
            "🏠 *Вибери дію:*\n"
            "• 📝 *Почати квіз* — створюй картки зі слів\n"
            "• 📊 *Статистика* — твій прогрес\n"
            "• 🌐 *Змінити мову* — вибери іншу мову"
        )
        try:
            if current_text != new_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=get_main_menu_inline_keyboard(),
                    parse_mode="MarkdownV2"
                )
            await callback.answer()
        except TelegramBadRequest as e:
            logging.error(f"Failed to edit message: {e}")
            await callback.answer()

    elif data == "repeat_quiz":
        state = user_state.get(chat_id, {})
        if state.get("stage") == "finished" and "words" in state:
            state["stage"] = "quiz"
            state["current_word_index"] = 0
            state["attempts"] = 3
            state["score"] = 0
            new_text = (
                "📍 *Квіз*\n"
                "🔄 *Починаємо заново\\!*"
            )
            try:
                if current_text != new_text:
                    await callback.message.edit_text(
                        new_text,
                        parse_mode="MarkdownV2"
                    )
                await send_next_word(chat_id)
            except TelegramBadRequest as e:
                logging.error(f"Failed to edit message: {e}")
                await send_next_word(chat_id)
        else:
            new_text = (
                "📍 *Помилка*\n"
                "❌ *Немає квіза для повтору\\!*"
            )
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
            except TelegramBadRequest as e:
                logging.error(f"Failed to edit message: {e}")
                await callback.answer()
        await callback.answer()

    elif data == "new_text":
        user_state[chat_id]["stage"] = "waiting_for_text"
        new_text = (
            "📍 *Введення тексту*\n"
            "📝 *Надішли новий текст або посилання для аналізу:*"
        )
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
        except TelegramBadRequest as e:
            logging.error(f"Failed to edit message: {e}")
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
                    "📍 *Введення тексту*\n"
                    "❌ *Не вдалося витягти текст із посилання\\.*",
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
                f"📍 *Підготовка квіза*\n"
                f"✨ *Я знайшов ключові слова:* _{', '.join(words)}_\\.\n"
                f"Готовий почати квіз? 🚀",
                parse_mode="MarkdownV2"
            )
            if len(words) < 5:
                await message.answer(
                    f"📍 *Попередження*\n"
                    "⚠️ Знайдено мало слів\\. Можливо, текст надто короткий\\.\n"
                    "Усе одно продовжимо\\!",
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
                "📍 *Введення тексту*\n"
                "❌ *Не вдалося знайти важливі слова\\.*",
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
            f"📍 *Квіз*\n"
            f"{progress}\n"
            f"Переклади слово _*{word}*_ українською:\n"
            f"Спроби: *{state['attempts']}*",
            parse_mode="MarkdownV2",
            reply_markup=get_back_and_main_menu_keyboard()
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
        save_quiz_result(chat_id, word, True)  # Змінили 1 на True
        await bot.send_message(
            chat_id,
            f"📍 *Квіз*\n"
            f"✅ *Правильно\\!* 🎉\n"
            f"Переходимо до наступного слова\\!",
            parse_mode="MarkdownV2"
        )
        await send_next_word(chat_id)
    else:
        state["attempts"] -= 1
        if state["attempts"] > 0:
            progress = f"*Слово {state['current_word_index'] + 1}/{state['total_words']}*"
            await bot.send_message(
                chat_id,
                f"📍 *Квіз*\n"
                f"{progress}\n"
                f"❌ *Неправильно\\.*\n"
                f"Спроби: *{state['attempts']}*",
                parse_mode="MarkdownV2",
                reply_markup=get_back_and_main_menu_keyboard()
            )
        else:
            state["current_word_index"] += 1
            state["attempts"] = 3
            save_quiz_result(chat_id, word, False)  # Змінили 0 на False
            await bot.send_message(
                chat_id,
                f"📍 *Квіз*\n"
                f"⏳ *Спроби закінчились\\!*\n"
                f"Правильний переклад: _*{correct_translation}*_\\.",
                parse_mode="MarkdownV2"
            )
            await send_next_word(chat_id)


async def finish_quiz(chat_id):
    state = user_state[chat_id]
    score = state["score"]
    total = state["total_words"]
    total_words, correct_answers = get_user_stats(chat_id)
    await bot.send_message(
        chat_id,
        f"📍 *Результат квіза*\n"
        f"🏁 *Квіз завершено\\!*\n"
        f"Твій результат: *{score}/{total}*\n"
        f"Вивчено слів: *{total_words}*\n"
        f"Правильних відповідей: *{correct_answers}*",
        reply_markup=get_finish_inline_keyboard(),
        parse_mode="MarkdownV2"
    )
    state["stage"] = "finished"


@app.route('/webhook', methods=['POST'])
async def webhook():
    update = types.Update(**request.get_json())
    await dp.feed_update(bot, update)
    return '', 200


async def set_webhook():
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("WEBHOOK_URL is not set in environment variables")
    await bot.set_webhook(webhook_url)
    logging.info(f"Webhook set to {webhook_url}")


async def main():
    # Ініціалізація бази даних
    init_db()

    if IS_LOCAL:
        # Локальний запуск із polling
        logging.info("Running in local mode with polling...")
        await dp.start_polling(bot)
    else:
        # Запуск на хостингу з webhook
        logging.info("Running in production mode with webhook...")
        await set_webhook()
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))


if __name__ == "__main__":
    asyncio.run(main())
