"""Application configuration."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings."""
    
    APP_NAME: str = "ChatShield"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    HOST: str = "localhost"
    PORT: int = 8000
    
    # Auth
    SECRET_KEY: str = "super-secret-key-change-this-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
