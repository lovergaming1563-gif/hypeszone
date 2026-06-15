import asyncio
import uvicorn
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)

from config import settings
from database.database import init_db
from handlers.user_handlers import start, handle_user_message
from handlers.admin_handlers import admin_stats, admin_inbox, handle_admin_callback, handle_admin_reply
from handlers.error_handlers import error_handler
from utils.logger import logger

# FastAPI App for Health Checks & Uptime Monitoring
app = FastAPI(title="Support Inbox API")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/ping")
async def ping():
    return "pong"

def build_bot_app():
    if not settings.BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing in the environment variables.")
        
    application = (
        ApplicationBuilder()
        .token(settings.BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .build()
    )
    
    # User Handlers
    application.add_handler(CommandHandler("start", start))
    
    # Admin Handlers
    application.add_handler(CommandHandler("inbox", admin_inbox))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^(viewchat_|back_inbox|areply_|aclose_|aban_)"))
    
    # Message Handlers
    
    # 1. Private Chat Admin Reply Handler
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.REPLY & ~filters.COMMAND, 
        handle_admin_reply
    ))
    
    # 2. User sending messages in DM
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & ~filters.COMMAND, 
        handle_user_message
    ))
    
    # Global Error Handler
    application.add_error_handler(error_handler)
    
    return application

async def start_services():
    # Initialize the database
    await init_db()
    
    # Initialize and start the Telegram Bot
    bot_app = build_bot_app()
    await bot_app.initialize()
    await bot_app.start()
    
    # Start polling for Telegram updates
    await bot_app.updater.start_polling(drop_pending_updates=True)
    logger.info("Private Support Inbox Bot Started Successfully")
    
    # Start FastAPI server
    config = uvicorn.Config(app, host="0.0.0.0", port=settings.PORT, log_level="warning")
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except asyncio.CancelledError:
        pass
    finally:
        # Graceful shutdown
        logger.info("Shutting down bot...")
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
