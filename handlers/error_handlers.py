from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import logger

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    # You can add logic here to notify developers/admins via Telegram
