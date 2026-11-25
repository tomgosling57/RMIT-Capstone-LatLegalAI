from typing import Optional
import os


class MockOAuthResponse:
    """Mock OAuth response with a redirect URL."""

    def __init__(self):
        self.url = "/auth/oauth/callback?token=mock-oauth-token"


class MockAuth:
    """Mock authentication class for Supabase when not configured."""

    def sign_in_with_password(self, credentials: dict) -> object:
        """Mock sign in with password."""
        return MockUserResponse()

    def sign_up(self, credentials: dict) -> object:
        """Mock sign up."""
        return MockUserResponse()

    def sign_in_with_oauth(self, credentials: dict) -> object:
        """Mock OAuth sign in."""
        return MockOAuthResponse()

    def sign_out(self) -> None:
        """Mock sign out."""
        pass

    def get_user(self, token: str) -> Optional[object]:
        """Mock get user."""
        return MockUserResponse()


class MockUserResponse:
    """Mock user response object."""

    def __init__(self):
        self.user = MockUser()
        self.session = MockSession()


class MockUser:
    """Mock user object."""

    def __init__(self):
        self.id = "mock-user-id"
        self.email = "mock@example.com"
        self.user_metadata = {"plan": "free"}


class MockSession:
    """Mock session object."""

    def __init__(self):
        self.access_token = "mock-access-token"


class MockSupabase:
    """Mock Supabase client for development when credentials are not configured."""

    def __init__(self):
        self.auth = MockAuth()


# Check if Supabase is configured, otherwise use mock
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if SUPABASE_URL and SUPABASE_KEY:
    from supabase import create_client, Client

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = MockSupabase()


def verify_session(token: str) -> dict | None:
    """Verify a Supabase JWT token and return user data."""
    try:
        user = supabase.auth.get_user(token)
        if user and user.user:
            return {
                "user_id": user.user.id,
                "email": user.user.email,
                "plan": user.user.user_metadata.get("plan", "free"),
            }
    except Exception:
        return None
    return None


def is_mock() -> bool:
    """Check if we're using the mock Supabase client."""
    return not (SUPABASE_URL and SUPABASE_KEY)
