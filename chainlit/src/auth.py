"""
LatMatrix Authentication Module - Password and OAuth authentication handlers.

Manages Chainlit password-auth callback, OAuth callback, and logout
cleanup for the LatMatrix Chainlit application.
"""

__all__ = [
    "auth_callback",
    "oauth_callback",
    "on_logout",
]



import os
from typing import Optional

import chainlit as cl
from fastapi import Request, Response
from chainlit.data import get_data_layer as _get_data_layer

# Development-only admin credentials from environment (or defaults).
# WARNING: These hardcoded defaults are for local development only.
_ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
_IS_DEV = os.environ.get("CHAINLIT_ENV", "development") != "production"


@cl.password_auth_callback
async def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """Password auth handler for login."""
    if _IS_DEV and username == _ADMIN_USERNAME and password == _ADMIN_PASSWORD:
        user = cl.User(identifier=username, metadata={"role": "ADMIN"})
        # Persist the user in the SQLite data layer to avoid
        # "Error fetching threads: User not found"
        data_layer = _get_data_layer()
        await data_layer.create_user(user)
        return user
    return None


@cl.oauth_callback
async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    """OAuth callback handler for third-party authentication providers."""
    if _IS_DEV:
        # Dev mode: accept any OAuth attempt as a mock dev user.
        user = cl.User(
            identifier="dev_user",
            metadata={"role": "DEV", "provider": provider_id},
        )
    else:
        # Production: use the real OAuth user data.
        user = cl.User(
            identifier=default_user.identifier,
            metadata={"role": "USER", **raw_user_data},
        )
    data_layer = _get_data_layer()
    await data_layer.create_user(user)
    return user


# Cookies that Chainlit / this application may set on login.
_LOGOUT_COOKIE_PREFIXES = ("chainlit-", "access_token", "refresh_token")


@cl.on_logout
def on_logout(request: Request, response: Response) -> None:
    """Handler to tidy up resources -- clear application cookies on logout."""
    for cookie_name in request.cookies.keys():
        if any(cookie_name.startswith(prefix) for prefix in _LOGOUT_COOKIE_PREFIXES):
            response.delete_cookie(cookie_name)
