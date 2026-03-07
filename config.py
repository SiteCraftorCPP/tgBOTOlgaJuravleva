import os
from dotenv import load_dotenv

load_dotenv()

# Данные для продакшена (VPS). Переопределяются через .env при необходимости.
BOT_TOKEN = os.getenv("BOT_TOKEN", "8689285232:AAFE_tjFWwtTEmvPrfgd281y69W-IvOAjUM")
CHAT_ID = int(os.getenv("CHAT_ID", "-1003786647693"))

# Список ID админов (через запятую в .env: ADMIN_IDS=480110890,6933111964)
_admin_ids_str = os.getenv("ADMIN_IDS", "480110890,6933111964")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_str.split(",") if x.strip()]

DB_NAME = os.getenv("DB_NAME", "bot_database.db")
