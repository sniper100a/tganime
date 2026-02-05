# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from typing import List
from config import ADMINS

# -----------------------------
# Главное меню
# -----------------------------
def main_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    """
    Главное меню.
    Админ видит кнопку '👑 Админ-панель'.
    """
    buttons = [
        [KeyboardButton(text="🎬 Просмотреть аниме"), KeyboardButton(text="🔎 Поиск")],
        [KeyboardButton(text="🧾 Жанры"), KeyboardButton(text="❤️ Избранное")]
    ]

    if user_id in ADMINS:
        buttons.append([KeyboardButton(text="👑 Админ-панель")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

# -----------------------------
# Меню администратора
# -----------------------------
def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить аниме"), KeyboardButton(text="✏️ Редактировать аниме")],
            [KeyboardButton(text="❌ Удалить аниме"), KeyboardButton(text="📋 Список всех аниме")],
            [KeyboardButton(text="🔙 В главное")]
        ],
        resize_keyboard=True
    )

# -----------------------------
# Кнопка возврата в главное меню
# -----------------------------
def back_to_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 В главное")]],
        resize_keyboard=True
    )

# -----------------------------
# Inline-клавиатура для аниме
# -----------------------------
def anime_inline_kb(anime_id: int, is_fav: bool = False) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👁 Смотреть", callback_data=f"watch:{anime_id}"),
            InlineKeyboardButton(text="❤️ В избранном" if is_fav else "🤍 Добавить в избранное", callback_data=f"fav:{anime_id}")
        ],
        [
            InlineKeyboardButton(text="⬅ Назад", callback_data=f"nav:{anime_id}:prev"),
            InlineKeyboardButton(text="➡ Вперед", callback_data=f"nav:{anime_id}:next")
        ]
    ])

# -----------------------------
# Простая inline-кнопка
# -----------------------------
def simple_inline(text: str, callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback)]]
    )

# -----------------------------
# Inline-клавиатура для жанров
# -----------------------------
def genres_list_inline(genres: List[tuple]) -> InlineKeyboardMarkup:
    """
    genres: List of (id, name)
    """
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"genre:{gid}")] for gid, name in genres]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
