from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, func, desc, update
from database.database import async_session
from models import User, Chat, Message
from datetime import datetime

class DBService:
    @staticmethod
    async def get_or_create_user(user_id: int, username: str = None) -> User:
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(id=user_id, username=username)
                session.add(user)
                # Also create a chat entry for the user
                chat = Chat(id=user_id)
                session.add(chat)
                await session.commit()
                await session.refresh(user)
            else:
                if user.username != username:
                    user.username = username
                    await session.commit()
            return user

    @staticmethod
    async def get_chat(user_id: int) -> Chat:
        async with async_session() as session:
            stmt = select(Chat).where(Chat.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def update_chat_status(user_id: int, status: str, reset_unread: bool = False):
        async with async_session() as session:
            stmt = update(Chat).where(Chat.id == user_id).values(
                status=status,
                updated_at=datetime.utcnow()
            )
            if reset_unread:
                stmt = stmt.values(unread_count=0)
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def add_message(chat_id: int, sender_id: int, text: str = None, 
                          media_type: str = "text", media_file_id: str = None, 
                          is_from_user: bool = True) -> Message:
        async with async_session() as session:
            msg = Message(
                chat_id=chat_id,
                sender_id=sender_id,
                text=text,
                media_type=media_type,
                media_file_id=media_file_id,
                is_from_user=is_from_user
            )
            session.add(msg)
            
            # Update chat
            chat_stmt = select(Chat).where(Chat.id == chat_id)
            chat_result = await session.execute(chat_stmt)
            chat = chat_result.scalar_one_or_none()
            if chat:
                chat.updated_at = datetime.utcnow()
                chat.status = "open"
                if is_from_user:
                    chat.unread_count += 1
            
            await session.commit()
            await session.refresh(msg)
            return msg

    @staticmethod
    async def is_user_banned(user_id: int) -> bool:
        async with async_session() as session:
            stmt = select(User.is_banned).where(User.id == user_id)
            result = await session.execute(stmt)
            is_banned = result.scalar_one_or_none()
            return bool(is_banned)
            
    @staticmethod
    async def ban_user(user_id: int, ban: bool = True):
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                user.is_banned = ban
                await session.commit()

    @staticmethod
    async def get_inbox_chats() -> list[Chat]:
        async with async_session() as session:
            # Get chats with their associated users, sorted by updated_at desc
            stmt = select(Chat).options(joinedload(Chat.user)).order_by(
                desc(Chat.updated_at)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_chat_history(chat_id: int, limit: int = 10) -> list[Message]:
        async with async_session() as session:
            stmt = select(Message).where(Message.chat_id == chat_id).order_by(desc(Message.created_at)).limit(limit)
            result = await session.execute(stmt)
            messages = result.scalars().all()
            return messages[::-1] # Return in chronological order

    @staticmethod
    async def get_stats() -> dict:
        async with async_session() as session:
            total_users = await session.scalar(select(func.count(User.id)))
            open_chats = await session.scalar(select(func.count(Chat.id)).where(Chat.status == "open"))
            closed_chats = await session.scalar(select(func.count(Chat.id)).where(Chat.status == "closed"))
            total_messages = await session.scalar(select(func.count(Message.id)))
            
            return {
                "total_users": total_users or 0,
                "open_chats": open_chats or 0,
                "closed_chats": closed_chats or 0,
                "total_messages": total_messages or 0
            }
