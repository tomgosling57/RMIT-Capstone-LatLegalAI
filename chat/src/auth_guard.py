"""
Authentication guard for the Streamlit Chat Service.

Provides ``require_auth()`` which must be called at the top of every Streamlit
page that requires authentication.

If Supabase credentials (``SUPABASE_URL`` / ``SUPABASE_KEY``) are **not**
configured, the guard enters a **stub mode**:
  - A warning is displayed on every page.
  - A fake "guest" user is returned so the UI still renders.
  - The chat service will **not** attempt to integrate with Supabase.

This allows local development and CI without a running Supabase instance.
"""

import streamlit as st
from supabase import create_client
import os

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")

_CREDENTIALS_CONFIGURED: bool = bool(SUPABASE_URL and SUPABASE_KEY)

# Only create the Supabase client if credentials are present
supabase = None
if _CREDENTIALS_CONFIGURED:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
LOGIN_URL = "/auth/login"


def credentials_configured() -> bool:
    """Return ``True`` if Supabase credentials are present in the environment."""
    return _CREDENTIALS_CONFIGURED


def check_credentials() -> None:
    """Check if Supabase credentials are configured.
    If not, display a streamlit warning."""
    if not credentials_configured():
        st.warning(
            "**Supabase credentials not configured.** "
            "Authentication is disabled. Set `SUPABASE_URL` and `SUPABASE_KEY` "
            "environment variables to enable user authentication.",
            icon="⚠️",
        )


def require_auth() -> dict | None:
    """Call at the top of every Streamlit page. Returns user info dict or None.

    **Normal mode** (credentials configured):
    1. If the user is already authenticated in session state, return cached data.
    2. Otherwise, read the Supabase JWT token from the URL query parameter
       (passed from Flask after a successful login/signup).
    3. Verify the token with Supabase and cache the user data in session state.
    4. Clear the token from the URL bar so it is not visible to the user.
    5. If no valid token is found, show an error and redirect to the login page.

    **Stub mode** (no credentials):
    - Display a persistent warning banner.
    - Return a fake "guest" user so the UI renders without Supabase.
    - The chat service will not attempt to call Supabase.
    """
    # ------------------------------------------------------------------
    # Stub mode — no Supabase credentials configured
    # ------------------------------------------------------------------
    if not _CREDENTIALS_CONFIGURED:
        if "user" not in st.session_state:
            st.session_state["user"] = {
                "user_id": "guest",
                "email": "guest@local.dev",
                "plan": "free",
            }
        return st.session_state["user"]

    # ------------------------------------------------------------------
    # Normal mode — credentials are present
    # ------------------------------------------------------------------

    # 1. Already authenticated in this session
    if "user" in st.session_state:
        return st.session_state["user"]

    # 2. Get token from query params (passed from Flask)
    token = st.query_params.get("token")

    if not token:
        st.error("Please log in to access the dashboard.")
        st.markdown(
            f'<meta http-equiv="refresh" content="1;url={LOGIN_URL}">',
            unsafe_allow_html=True,
        )
        st.stop()

    try:
        # 3. Verify the token with Supabase
        user = supabase.auth.get_user(token)  # type: ignore[union-attr]

        if user and user.user:
            user_data = {
                "user_id": user.user.id,
                "email": user.user.email,
                "plan": user.user.user_metadata.get("plan", "free"),
            }
            st.session_state["user"] = user_data
            st.session_state["supabase_token"] = token
            # 4. Remove token from URL bar
            st.query_params.clear()
            return user_data
    except Exception:
        pass

    # 5. Token invalid or expired
    st.error("Session token invalid or expired. Please log in again.")
    st.markdown(
        f'<meta http-equiv="refresh" content="1;url={LOGIN_URL}">',
        unsafe_allow_html=True,
    )
    st.stop()
