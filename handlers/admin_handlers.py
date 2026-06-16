import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes
from services.db_service import DBService
from config import settings
from utils.logger import logger

def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    stats = await DBService.get_stats()
    text = (
        "📊 <b>Support Inbox Analytics</b>\n\n"
        f"Total Users: {stats['total_users']}\n"
        f"Open Chats: {stats['open_chats']}\n"
        f"Closed Chats: {stats['closed_chats']}\n"
        f"Total Messages: {stats['total_messages']}\n"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def admin_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    chats = await DBService.get_inbox_chats()
    if not chats:
        await update.message.reply_text("Inbox is empty.")
        return

    keyboard = []
    for chat in chats:
        status_icon = "🔴" if chat.status == "open" else "🟢"
        unread_suffix = f" ({chat.unread_count})" if chat.unread_count > 0 else ""
        
        user_name = chat.user.username or f"User {chat.id}"
        btn_text = f"{status_icon} {user_name}{unread_suffix}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"viewchat_{chat.id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text("📥 <b>Support Inbox</b>", reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text("📥 <b>Support Inbox</b>", reply_markup=reply_markup, parse_mode="HTML")

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("Access denied.")
        return

    await query.answer()
    data = query.data

    if data.startswith("viewchat_"):
        user_id = int(data.split("_")[1])
        history = await DBService.get_chat_history(user_id)
        
        history_text = f"👤 <b>Conversation with {user_id}</b>\n\n"
        if not history:
            history_text += "<i>No messages yet.</i>"
        for msg in history:
            sender = "👤 User" if msg.is_from_user else "🛡️ Admin"
            content = msg.text or f"[{msg.media_type.upper()}]"
            history_text += f"<b>{sender}:</b> {content}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("✉️ Reply", callback_data=f"areply_{user_id}"),
                InlineKeyboardButton("✅ Close", callback_data=f"aclose_{user_id}")
            ],
            [InlineKeyboardButton("🔙 Back to Inbox", callback_data="back_inbox")]
        ]
        await query.edit_message_text(history_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "back_inbox":
        await admin_inbox(update, context)

    elif data.startswith("areply_"):
        user_id = int(data.split("_")[1])
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=f"Typing reply for User ID: <code>{user_id}</code>. Reply to this message with your response.",
            reply_markup=ForceReply(selective=True),
            parse_mode="HTML"
        )

    elif data.startswith("aclose_"):
        user_id = int(data.split("_")[1])
        await DBService.update_chat_status(user_id, "closed", reset_unread=True)
        await query.message.reply_text(f"✅ Chat with {user_id} closed.")
        # Go back to inbox
        await admin_inbox(update, context)

    elif data.startswith("aban_"):
        user_id = int(data.split("_")[1])
        await DBService.ban_user(user_id, True)
        await query.message.reply_text(f"🚫 User {user_id} has been banned.")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    if not is_admin(admin_id):
        return

    logger.info(f"Admin {admin_id} is attempting to send a reply...")

    # Check if it's a reply to our ForceReply message
    if not update.message.reply_to_message:
        logger.info("Admin message is not a reply to a bot message (no reply_to_message).")
        return

    reply_to = update.message.reply_to_message
    original_text = reply_to.text or reply_to.caption or ""
    
    # Improved regex to match "User ID: 123" or "Conversation with 123"
    match = re.search(r"(?:User ID|Conversation with)[:\s]+(\d+)", original_text, re.IGNORECASE)
    if not match:
        logger.warning(f"Admin replied to a message but no target ID found. Text: {original_text[:50]}...")
        # Optional: Let the admin know they replied to the wrong message
        await update.message.reply_text("❌ Could not find User ID in the message you replied to. Please reply to the bot's prompt or the conversation header.")
        return

    target_user_id = int(match.group(1))
    logger.info(f"Admin {admin_id} targeting User ID: {target_user_id}")
    
    # Save admin message
    text_content = update.message.text or update.message.caption or ""
    media_type = "text"
    media_file_id = None
    
    # [Rest of media detection logic remains the same...]
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

    try:
        await DBService.add_message(
            target_user_id, admin_id, text=text_content, 
            media_type=media_type, media_file_id=media_file_id, is_from_user=False
        )
        
        # Reset unread count when admin replies
        await DBService.update_chat_status(target_user_id, "open", reset_unread=True)

        # Send to user
        await update.message.copy(chat_id=target_user_id)
        logger.info(f"✅ Successfully sent admin reply to User ID: {target_user_id}")
        await update.message.reply_text(f"✅ Reply sent to User ID: {target_user_id}.")
    except Exception as e:
        logger.error(f"❌ Failed to send reply to user {target_user_id}: {e}")
        await update.message.reply_text(f"❌ Failed to send reply: {e}")
