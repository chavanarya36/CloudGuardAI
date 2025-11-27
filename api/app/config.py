from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql://cloudguard:cloudguard@localhost:5432/cloudguard"
    redis_url: str = "redis://localhost:6379/0"
    ml_service_url: str = "http://ml-service:8001"
    secret_key: str = "change-this-secret-key-in-production"
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"


settings = Settings()
