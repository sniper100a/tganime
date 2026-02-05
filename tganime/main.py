# main.py
import asyncio
from handlers import dp, bot
from database import init_db
from config import POSTERS_DIR
import os

async def main():
    # ensure posters dir
    os.makedirs(POSTERS_DIR, exist_ok=True)
    await init_db()
    print("Бот запустился...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
