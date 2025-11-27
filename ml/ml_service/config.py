from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    ml_models_path: str = "../models_artifacts"
    rules_path: str = "../rules_engine"
    features_path: str = "../features_artifacts"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_provider: str = "openai"
    
    class Config:
        env_file = ".env"


settings = Settings()
