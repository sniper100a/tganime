# utils.py
import os
from config import POSTERS_DIR
from aiogram import Bot
import aiofiles

# Убедиться, что папка для постеров существует
os.makedirs(POSTERS_DIR, exist_ok=True)

# -----------------------------
# Форматирование карточки аниме
# -----------------------------
def format_anime_card(anime: dict) -> str:
    """
    anime: dict с ключами title, description, year, rating, genres, watch_url
    Возвращает текстовую карточку для отправки пользователю.
    """
    genres = ", ".join(anime.get("genres", [])) if anime.get("genres") else "—"
    text = f"*{anime.get('title', '—')}* ({anime.get('year','—')})\n\n"
    text += f"Жанры: _{genres}_\n"
    text += f"Рейтинг: {anime.get('rating', '—')}\n\n"

    desc = anime.get("description") or ""
    if len(desc) > 800:
        desc = desc[:800] + "…"
    text += desc
    return text

# -----------------------------
# Скачивание и сохранение фото
# -----------------------------
async def save_photo_locally(bot: Bot, file_id: str, filename_hint: str) -> str:
    """
    Скачивает файл по file_id и сохраняет в POSTERS_DIR.
    Возвращает путь к файлу.
    filename_hint используется для формирования имени файла.
    """
    # безопасное имя файла
    safe_name = "".join([c if c.isalnum() else "_" for c in filename_hint])[:40]
    path = os.path.join(POSTERS_DIR, f"{safe_name}_{file_id}.jpg")

    # если файл уже есть — вернуть путь
    if os.path.exists(path):
        return path

    # иначе скачать файл
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, destination=path)
    return path
