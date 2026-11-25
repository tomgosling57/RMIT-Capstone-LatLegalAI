import logging
import os

from flask import Flask, g
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from .auth.routes import auth_bp, limiter
from .main.routes import main_bp
from .upload.routes import upload_bp
from .auth.supabase_client import is_mock

_CHAT_URL = os.environ.get("CHAT_EXTERNAL_URL", "http://localhost/chat")

logger = logging.getLogger(__name__)


def _warn_missing_env_vars(app):
    """Log clear warnings for any missing or stub environment variables at startup."""
    warnings = []

    secret_key = os.environ.get("SECRET_KEY", "")
    if not secret_key or secret_key == "dev-secret-change-me":
        warnings.append(
            "SECRET_KEY is not set or is using the insecure default "
            "'dev-secret-change-me'. Set SECRET_KEY in your .env file."
        )

    if not os.environ.get("SUPABASE_URL", ""):
        warnings.append(
            "SUPABASE_URL is not set. Authentication is running in STUB/MOCK mode. "
            "Set SUPABASE_URL in your .env file when "
            "Supabase credentials are available."
        )

    if not os.environ.get("SUPABASE_KEY", ""):
        warnings.append(
            "SUPABASE_KEY is not set. Authentication is running in STUB/MOCK mode. "
            "Set SUPABASE_KEY in your .env file when "
            "Supabase credentials are available."
        )

    if warnings:
        logger.warning("=" * 70)
        logger.warning("CONFIGURATION WARNINGS — app is running in stub/dev mode:")
        for i, msg in enumerate(warnings, 1):
            logger.warning("  [%d] %s", i, msg)
        logger.warning("=" * 70)


def create_app(config_object="config.Config"):
    """Application factory."""
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_object)

    # Trust the X-Forwarded-* headers set by nginx so that url_for with
    # _external=True and redirect() generate correct absolute URLs
    # (e.g. http://localhost/chat instead of http://localhost:5000/chat).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Emit startup warnings for missing/stub configuration
    _warn_missing_env_vars(app)

    # Security headers via Flask-Talisman
    Talisman(
        app,
        content_security_policy={
            "default-src": "'self'",
            "script-src": ["'self'", "'unsafe-inline'"],  # htmx needs this
            "style-src": [
                "'self'",
                "'unsafe-inline'",
                "https://fonts.googleapis.com",
            ],  # inline <style> + Google Fonts stylesheet
            "img-src": ["'self'", "data:"],  # base64-encoded images (OAuth logos)
            "font-src": ["'self'", "https://fonts.gstatic.com"],  # Google Fonts
            "connect-src": ["'self'", "https://*.supabase.co"],  # Supabase API + OAuth
        },
        force_https=False,  # Disable HTTPS redirect - nginx handles SSL termination
    )

    # Rate limiting via Flask-Limiter (backed by Redis)
    limiter.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp)

    # Store supabase stub status on Flask's request context (g) rather than
    # session so it works even when SECRET_KEY is not yet configured.
    @app.before_request
    def check_supabase_config():
        g.supabase_configured = not is_mock()

    @app.context_processor
    def inject_globals():
        return {"chat_url": _CHAT_URL}

    return app
