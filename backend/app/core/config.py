"""
Application Configuration

Environment-based settings for VoxTrace backend
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "VoxTrace"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/db/voxtrace.db"

    # File Storage
    UPLOAD_DIR: str = "./data/uploads"
    PROCESSED_DIR: str = "./data/processed"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB

    # Model Settings (Phase 1: Not loaded)
    MODEL_DIR: str = "./models"
    ENABLE_ASR: bool = False
    ENABLE_DIARIZATION: bool = False
    ENABLE_VAD: bool = False
    ENABLE_ENHANCEMENT: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
