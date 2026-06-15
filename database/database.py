from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from config import DATABASE_URL
from utils.logger import logger

# Convert postgresql:// to postgresql+asyncpg:// if necessary for production migration
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True
)

async_session = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

Base = declarative_base()

async def init_db():
    from models.schema import Base
    async with engine.begin() as conn:
        logger.info("Initializing Database...")
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
