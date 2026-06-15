from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True) # Telegram User ID
    username = Column(String, nullable=True)
    is_banned = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    chat = relationship("Chat", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Staff(Base):
    __tablename__ = "staff"
    
    id = Column(Integer, primary_key=True, index=True) # Telegram User ID
    username = Column(String, nullable=True)
    role = Column(String, default="admin") # admin, moderator
    joined_at = Column(DateTime, default=datetime.utcnow)

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, ForeignKey("users.id"), primary_key=True, index=True) # Same as User ID
    status = Column(String, default="closed") # open, closed
    unread_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="chat")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender_id = Column(Integer) # Either user_id or staff_id or bot_id
    text = Column(Text, nullable=True)
    media_type = Column(String, nullable=True) # text, photo, video, document, voice, sticker, audio
    media_file_id = Column(String, nullable=True)
    is_from_user = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    chat = relationship("Chat", back_populates="messages")
