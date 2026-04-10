import os
from typing import Optional
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()

# Данные для продакшена (VPS). Переопределяются через .env при необходимости.
BOT_TOKEN = os.getenv("BOT_TOKEN", "8689285232:AAFE_tjFWwtTEmvPrfgd281y69W-IvOAjUM")
CHAT_ID = int(os.getenv("CHAT_ID", "-1003786647693"))

# Список ID админов (через запятую в .env: ADMIN_IDS=480110890,6933111964)
_admin_ids_str = os.getenv("ADMIN_IDS", "480110890,6933111964")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_str.split(",") if x.strip()]

DB_NAME = os.getenv("DB_NAME", "bot_database.db")


def normalize_telegram_proxy(raw: Optional[str]) -> Optional[str]:
    """Нормализовать прокси для Telegram API.

    Поддерживаем:
    - socks5://user:pass@host:port (или http://...)
    - host:port:user:pass (как в панелях прокси)
    """
    s = (raw or "").strip()
    if not s:
        return None
    if "://" in s:
        return s
    parts = s.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        user_q = quote(user, safe="")
        pass_q = quote(password, safe="")
        return f"socks5://{user_q}:{pass_q}@{host}:{port}"
    return s


# TELEGRAM_PROXY в .env — если пусто, бот идёт напрямую (как на VPS)
TELEGRAM_PROXY_URL = normalize_telegram_proxy(os.getenv("TELEGRAM_PROXY"))
