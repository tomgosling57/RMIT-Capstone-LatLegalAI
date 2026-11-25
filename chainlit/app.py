"""
LatMatrix Chainlit Application — Thin Entry Point.

This module is the Chainlit entry point (used by ``chainlit run app.py``).
It re-exports the lifecycle hooks registered in ``src.app`` so that Chainlit
discovers them via normal package-based import resolution, avoiding the
relative-import pitfalls that occur when loading ``src/app.py`` directly
by file path.

Chainlit discovers decorated callbacks (``@cl.on_chat_start``, etc.) by
scanning the loaded module's namespace after import. By importing from
``src.app`` here, those symbols become available in this module's scope.
"""

# Import auth first so that @cl.password_auth_callback, @cl.oauth_callback
# and @cl.on_logout decorators execute and register themselves in Chainlit's
# global config. Without this import the login page is never displayed.
import src.auth as auth
import src.database as db
from src.app import (
    on_chat_start,
    on_settings_update,
    on_chat_resume,
    on_message,
    on_stop,
    on_chat_end,
    set_starters,
)

__all__ = [
    "on_chat_start",
    "on_settings_update",
    "on_chat_resume",
    "on_message",
    "on_stop",
    "on_chat_end",
    "set_starters",
]

# Suppress "unused import" warnings for side-effect-only imports.
# auth registers @cl.password_auth_callback and @cl.oauth_callback decorators.
# db registers the @cl.data_layer decorator and initialises the database schema.
_ = (auth, db)