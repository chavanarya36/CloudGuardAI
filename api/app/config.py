from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    database_url: str = "sqlite:///./cloudguard.db"
    redis_url: str = "redis://localhost:6379/0"
    ml_service_url: str = "http://localhost:8001"
    secret_key: str = "change-this-secret-key-in-production"
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173"
    ]
    debug: bool = False
    log_level: str = "INFO"


settings = Settings()

# Warn if using default secret key (log only — no warnings.warn to avoid CI noise)
if settings.secret_key == "change-this-secret-key-in-production":
    logger.warning("SECURITY: Default secret key detected. Set SECRET_KEY in environment.")
