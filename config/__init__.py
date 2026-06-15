from .settings import settings

# Expose settings fields for direct import compatibility
DATABASE_URL = settings.DATABASE_URL
LOG_LEVEL = settings.LOG_LEVEL
BOT_TOKEN = settings.BOT_TOKEN
ADMIN_IDS = settings.ADMIN_IDS
PORT = settings.PORT
MAX_MESSAGE_LENGTH = settings.MAX_MESSAGE_LENGTH
