from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Telegram Bot Configuration
    BOT_TOKEN: str
    ADMIN_IDS_RAW: str = "" # Comma-separated list of IDs in .env
    
    @property
    def ADMIN_IDS(self) -> list[int]:
        if not self.ADMIN_IDS_RAW:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS_RAW.split(",") if x.strip()]
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///support_bot.db"
    
    # Web Server
    PORT: int = 8080
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Constants
    MAX_MESSAGE_LENGTH: int = 4000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
settings = Settings()
