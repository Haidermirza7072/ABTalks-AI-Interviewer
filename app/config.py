import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "The Thread Puller Backend"
    ENV: str = "development"
    
    # LLM Settings
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_MODEL: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    LLM_TIMEOUT_SECONDS: float = 5.0
    
    # Session Persistence & TTL
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)
    SESSION_DIR: str = os.getenv("SESSION_DIR", "./tmp/sessions")
    SESSION_TTL_HOURS: int = 1
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # Data Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CURRICULUM_FILE: str = os.path.join(BASE_DIR, "data", "curriculum.json")
    CANDIDATE_FILE: str = os.path.join(BASE_DIR, "data", "candidate_profiles.json")
    FALLBACK_FILE: str = os.path.join(BASE_DIR, "data", "fallback_questions.json")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
