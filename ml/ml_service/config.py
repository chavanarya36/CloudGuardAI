from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    ml_models_path: str = "ml/models_artifacts"
    rules_path: str = "rules/rules_engine"
    features_path: str = "ml/features_artifacts"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_provider: str = "openai"


settings = Settings()
