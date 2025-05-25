from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_language_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇸 English", callback_data="lang:en"),
            InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang:ua")
        ],
        [
            InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="lang:de"),
            InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang:fr")
        ]
    ])
    return keyboard

def get_main_menu_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Почати квіз", callback_data="start_quiz")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="view_stats")],
        [InlineKeyboardButton(text="🌐 Змінити мову", callback_data="change_language")],
        [InlineKeyboardButton(text="ℹ️ Довідка", callback_data="show_help")]  # Нова кнопка
    ])
    return keyboard

def get_finish_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Повторити квіз", callback_data="repeat_quiz")],
        [InlineKeyboardButton(text="📝 Новий текст", callback_data="new_text")],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    return keyboard

def get_back_and_main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start_quiz")],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    return keyboard