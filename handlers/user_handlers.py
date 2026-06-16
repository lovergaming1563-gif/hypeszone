from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from services.db_service import DBService
from config import settings
from utils.logger import logger

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check/Create user and associated chat
    db_user = await DBService.get_or_create_user(user.id, user.username)
    if db_user.is_banned:
        return
        
    welcome_text = (
        "🎧 <b>Support Center</b>\n\n"
        "Send your message below.\n"
        "Our team will reply shortly."
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # SAFETY FALLBACK: If an admin sends a message, don't treat it as a ticket
    if user.id in settings.ADMIN_IDS:
        logger.info(f"Ignoring message from admin {user.id} in user_handler.")
        return
        
    if await DBService.is_user_banned(user.id):
        return

    # Determine media type
    media_type = "text"
    media_file_id = None
    if update.message.photo:
        media_type = "photo"
        media_file_id = update.message.photo[-1].file_id
    elif update.message.document:
        media_type = "document"
        media_file_id = update.message.document.file_id
    elif update.message.video:
        media_type = "video"
        media_file_id = update.message.video.file_id
    elif update.message.voice:
        media_type = "voice"
        media_file_id = update.message.voice.file_id
    elif update.message.audio:
        media_type = "audio"
        media_file_id = update.message.audio.file_id
    elif update.message.sticker:
        media_type = "sticker"
        media_file_id = update.message.sticker.file_id

    # Save message to DB (this also opens the chat and increments unread count)
    text_content = update.message.text or update.message.caption or ""
    try:
        await DBService.add_message(
            user.id, user.id, text=text_content, 
            media_type=media_type, media_file_id=media_file_id, is_from_user=True
        )
        logger.info(f"✅ Message saved to DB for User ID: {user.id}")
    except Exception as e:
        logger.error(f"❌ Failed to save message to DB: {e}")

    # Send confirmation to user
    try:
        await update.message.reply_text("✅ Your message has been sent to the support team.")
        logger.info(f"📤 Sent confirmation reply to User ID: {user.id}")
    except Exception as e:
        logger.error(f"❌ Failed to send confirmation reply to User ID: {user.id}: {e}")

    # Alert admins about new activity
    chat = await DBService.get_chat(user.id)
    # Only notify if this is the first unread message to avoid spamming for every single line in a burst
    if chat and chat.unread_count == 1:
        for admin_id in settings.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text="📩 <b>New msg receive check /inbox</b>",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
