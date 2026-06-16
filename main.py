import asyncio
import sys
import uvicorn
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)

# Initialize logging as early as possible
from utils.logger import logger
logger.info("Starting Support Bot Application...")

try:
    from config import settings
    from database.database import init_db
    from handlers.user_handlers import start, handle_user_message
    from handlers.admin_handlers import admin_stats, admin_inbox, handle_admin_callback, handle_admin_reply
    from handlers.error_handlers import error_handler
except Exception as e:
    logger.critical(f"Failed to import modules: {e}", exc_info=True)
    sys.exit(1)

# FastAPI App for Health Checks & Uptime Monitoring
app = FastAPI(title="Support Inbox API")

@app.get("/", methods=["GET", "HEAD"])
async def root():
    return {"message": "Support Bot API is running"}

@app.get("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok"}

@app.get("/ping", methods=["GET", "HEAD"])
async def ping():
    return "pong"

def build_bot_app():
    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN is missing in the environment variables.")
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
    try:
        # Initialize the database
        logger.info("Initializing database...")
        await init_db()
        
        # Initialize and start the Telegram Bot
        logger.info("Initializing Telegram bot...")
        bot_app = build_bot_app()
        await bot_app.initialize()
        await bot_app.start()
        
        # Start polling for Telegram updates
        await bot_app.updater.start_polling(drop_pending_updates=True)
        logger.info("Private Support Inbox Bot Started Successfully and Polling.")
        
        # Start FastAPI server
        logger.info(f"Starting FastAPI server on port {settings.PORT}...")
        config = uvicorn.Config(app, host="0.0.0.0", port=settings.PORT, log_level="info")
        server = uvicorn.Server(config)
        
        await server.serve()
    except Exception as e:
        logger.error(f"Error in start_services: {e}", exc_info=True)
        raise
    finally:
        # Graceful shutdown
        if 'bot_app' in locals():
            logger.info("Shutting down bot...")
            await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal crash: {e}", exc_info=True)
        sys.exit(1)
