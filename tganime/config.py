import os
from pathlib import Path
from dotenv import load_dotenv

# load .env from project root
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / '.env')

API_TOKEN = os.getenv('API_TOKEN') or ''

# ADMINS: comma-separated list in .env, fallback to single id
ADMINS = [int(x) for x in os.getenv('ADMINS', '985274710').split(',') if x]

POSTERS_DIR = os.path.join(os.path.dirname(__file__), "posters")

# SQLite default path
DB_PATH = os.getenv('DB_PATH') or os.path.join(os.path.dirname(__file__), "anime.db")

# Channel for autoposting (can be set by admin in bot)
AUTOPOST_CHANNEL = os.getenv('AUTOPOST_CHANNEL') or ""