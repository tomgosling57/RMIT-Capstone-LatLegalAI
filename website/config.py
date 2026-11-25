import os


class Config:
    """Base configuration for the Website Service (Flask)."""

    # Flask secret key — must be set via environment variable in production
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or "dev-secret-change-me"

    # Supabase credentials
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL") or ""
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY") or ""

    # AI Summarizer Service base URL
    API_URL: str = os.environ.get("API_URL", "http://localhost:8000")

    # Redis connection
    REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.environ.get("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.environ.get("REDIS_DB", "0"))

    # Flask-Limiter: Redis storage URI (db=2 reserved for rate-limit counters)
    RATELIMIT_STORAGE_URI: str = os.environ.get(
        "RATELIMIT_STORAGE_URI",
        f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:"
        f"{os.environ.get('REDIS_PORT', '6379')}/2",
    )
    RATELIMIT_STRATEGY: str = "fixed-window"

    # Session cookie security
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    # Set to True in production (requires HTTPS)
    SESSION_COOKIE_SECURE: bool = (
        os.environ.get("FLASK_ENV", "development") == "production"
    )

    # Flask environment
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "0") == "1"


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Configuration for testing — disables rate limiting."""

    TESTING = True
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    # Disable rate limiting in tests to avoid Redis dependency
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
