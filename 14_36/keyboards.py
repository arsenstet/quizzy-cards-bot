from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_language_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang:en")]
    ])
    return keyboard


def get_main_menu_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Почати квіз", callback_data="start_quiz")],
        [InlineKeyboardButton(text="📊 Переглянути статистику", callback_data="view_stats")],
        [InlineKeyboardButton(text="🌐 Змінити мову", callback_data="change_language")]
        # Місце для майбутньої кнопки "Вибрати тему" з кластеризацією
    ])
    return keyboard


def get_finish_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Повторити квіз", callback_data="repeat_quiz"),
            InlineKeyboardButton(text="📝 Новий текст", callback_data="new_text")
        ],
        [
            InlineKeyboardButton(text="📊 Переглянути статистику", callback_data="view_stats"),
            InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")
        ]
    ])
    return keyboard