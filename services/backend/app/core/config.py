"""Core configuration management using Pydantic settings."""
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-in-production"

    # Supabase - with defaults for testing
    SUPABASE_URL: str = "https://test.supabase.co"
    SUPABASE_ANON_KEY: str = "test-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "test-service-key"

    # Database - with defaults for testing
    DATABASE_URL: str = "postgresql://test:test@localhost/test"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://test:test@localhost/test"

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
    ]

    # OPETSE-27: TLS 1.3 Security Requirement
    ENABLE_TLS: bool = False
    SSL_CERTFILE: str = ""
    SSL_KEYFILE: str = ""

    # OPETSE-28: Strong Password Requirement (SRS S25)
    STRONG_PASSWORD_REQUIRED: bool = True
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL_CHAR: bool = True

    # OPETSE-29: Least-Privilege Access Control (SRS S26)
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    ENFORCE_LEAST_PRIVILEGE: bool = True

    # OPETSE-30: Automatic Session Timeout (SRS S27)
    SESSION_TIMEOUT_MINUTES: int = 15

    # OPETSE-10: Late Submissions for Special Cases (SRS S7)
    LATE_SUBMISSION_ENABLED: bool = True
    LATE_SUBMISSION_MAX_HOURS: int = 24

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
