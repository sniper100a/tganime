# config.py
import os

API_TOKEN = "7855851573:AAFM_HXFaQeeJxPcMVqfohqdMXv592b65_E"

# Список админских telegram user_id (целые числа)
ADMINS = [985274710]  # <- замени на свой id

# Папка для локального хранения постеров
POSTERS_DIR = os.path.join(os.path.dirname(__file__), "posters")

# Путь к базе
DB_PATH = os.path.join(os.path.dirname(__file__), "anime.db")
