import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    OWNER_USERNAME = os.getenv("OWNER_USERNAME", "your_username")
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", 0))
    BOT_NAME = os.getenv("BOT_NAME", "GETO")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "GetoBot")

    DURATION_MAP = {
        "s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800
    }
