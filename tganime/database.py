# database.py
import aiosqlite
import datetime
from typing import List, Optional
from config import DB_PATH

# -----------------------------
# Инициализация базы данных
# -----------------------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS anime (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            year INTEGER,
            rating REAL,
            poster_file_id TEXT,
            poster_path TEXT,
            watch_url TEXT,
            date_added TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS anime_genres (
            anime_id INTEGER,
            genre_id INTEGER,
            PRIMARY KEY (anime_id, genre_id),
            FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            anime_id INTEGER,
            PRIMARY KEY (user_id, anime_id),
            FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
        )""")
        await db.commit()

# -----------------------------
# Жанры
# -----------------------------
async def add_genre(name: str) -> int:
    name = name.strip()
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            cur = await db.execute("INSERT INTO genres(name) VALUES(?)", (name,))
            await db.commit()
            return cur.lastrowid
        except aiosqlite.IntegrityError:
            row = await db.execute_fetchone("SELECT id FROM genres WHERE name=?", (name,))
            return row[0]

async def list_genres() -> List[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, name FROM genres ORDER BY name")
        return await cur.fetchall()

# -----------------------------
# Аниме
# -----------------------------
async def add_anime(title: str, description: str, year: int, rating: float, poster_file_id: str, poster_path: str, watch_url: str, genre_ids: List[int]) -> int:
    date_added = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO anime(title, description, year, rating, poster_file_id, poster_path, watch_url, date_added) VALUES(?,?,?,?,?,?,?,?)",
            (title, description, year, rating, poster_file_id, poster_path, watch_url, date_added)
        )
        anime_id = cur.lastrowid
        for gid in genre_ids:
            await db.execute("INSERT OR IGNORE INTO anime_genres(anime_id, genre_id) VALUES(?,?)", (anime_id, gid))
        await db.commit()
        return anime_id

async def get_anime(anime_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, title, description, year, rating, poster_file_id, poster_path, watch_url, date_added FROM anime WHERE id=?",
            (anime_id,)
        )
        row = await cur.fetchone()
        if not row:
            return None
        anime = dict(zip(["id","title","description","year","rating","poster_file_id","poster_path","watch_url","date_added"], row))
        # Жанры
        cur = await db.execute("""
            SELECT g.id, g.name FROM genres g
            JOIN anime_genres ag ON ag.genre_id = g.id
            WHERE ag.anime_id = ? ORDER BY g.name
        """, (anime_id,))
        genres = await cur.fetchall()
        anime["genres"] = [g[1] for g in genres]
        anime["genre_ids"] = [g[0] for g in genres]
        return anime

async def list_all_anime() -> List[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, title, year, rating FROM anime ORDER BY id DESC")
        return await cur.fetchall()

async def search_anime_by_title(term: str) -> List[tuple]:
    term = f"%{term}%"
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, title FROM anime WHERE title LIKE ? ORDER BY title", (term,))
        return await cur.fetchall()

async def list_anime_by_genre(genre_id: int) -> List[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            SELECT a.id, a.title FROM anime a
            JOIN anime_genres ag ON ag.anime_id = a.id
            WHERE ag.genre_id = ? ORDER BY a.title
        """, (genre_id,))
        return await cur.fetchall()

async def update_anime_field(anime_id: int, field: str, value):
    if field not in ("title","description","year","rating","poster_file_id","poster_path","watch_url"):
        raise ValueError("Invalid field")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE anime SET {field} = ? WHERE id = ?", (value, anime_id))
        await db.commit()

async def set_anime_genres(anime_id: int, genre_ids: List[int]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM anime_genres WHERE anime_id = ?", (anime_id,))
        for gid in genre_ids:
            await db.execute("INSERT INTO anime_genres(anime_id, genre_id) VALUES(?,?)", (anime_id, gid))
        await db.commit()

async def delete_anime(anime_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM anime WHERE id = ?", (anime_id,))
        await db.commit()

# -----------------------------
# Избранное
# -----------------------------
async def add_favorite(user_id: int, anime_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO favorites(user_id, anime_id) VALUES(?,?)", (user_id, anime_id))
        await db.commit()

async def remove_favorite(user_id: int, anime_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM favorites WHERE user_id = ? AND anime_id = ?", (user_id, anime_id))
        await db.commit()

async def list_favorites(user_id: int) -> List[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            SELECT a.id, a.title FROM anime a
            JOIN favorites f ON f.anime_id = a.id
            WHERE f.user_id = ? ORDER BY a.title
        """, (user_id,))
        return await cur.fetchall()
