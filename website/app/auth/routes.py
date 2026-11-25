import base64
import os
from pathlib import Path

from flask import Blueprint, render_template, redirect, url_for, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .supabase_client import supabase

auth_bp = Blueprint("auth", __name__)

limiter = Limiter(key_func=get_remote_address)

# External URL for the Chainlit chat app (served by nginx on port 80).
# When the user is behind nginx, Flask's relative redirect to /chat would stay
# on the current port (e.g. :5000).  This absolute URL ensures the browser
# goes through nginx on port 80.
_CHAT_URL = os.environ.get("CHAT_EXTERNAL_URL", "http://localhost/chat")


# Load and encode images to base64
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# Get the directory of the current file and construct paths
current_dir = Path(__file__).parent.parent
google_logo_b64 = get_image_base64(str(current_dir / "static" / "GoogleLogo.png"))
facebook_logo_b64 = get_image_base64(str(current_dir / "static" / "FacebookLogo.png"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Redirect directly to Chainlit for login."""
    return redirect(_CHAT_URL)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Redirect directly to Chainlit for signup."""
    return redirect(_CHAT_URL)


@auth_bp.route("/logout")
def logout():
    token = session.get("supabase_token")
    if token:
        supabase.auth.sign_out()
    session.clear()
    return redirect(url_for("main.home"))


@auth_bp.route("/oauth/google")
def oauth_google():
    """Initiate Google OAuth login via Supabase."""
    try:
        redirect_url = url_for("auth.oauth_callback", _external=True)
        response = supabase.auth.sign_in_with_oauth(
            {"provider": "google", "options": {"redirect_to": redirect_url}}
        )
        if response and hasattr(response, "url"):
            return redirect(response.url)
    except Exception as e:
        return render_template(
            "auth.html",
            error=f"Google OAuth failed: {e}",
            tab="login",
            google_logo_b64=google_logo_b64,
            facebook_logo_b64=facebook_logo_b64,
        )
    return redirect(url_for("auth.login"))


@auth_bp.route("/oauth/facebook")
def oauth_facebook():
    """Initiate Facebook OAuth login via Supabase."""
    try:
        redirect_url = url_for("auth.oauth_callback", _external=True)
        response = supabase.auth.sign_in_with_oauth(
            {"provider": "facebook", "options": {"redirect_to": redirect_url}}
        )
        if response and hasattr(response, "url"):
            return redirect(response.url)
    except Exception as e:
        return render_template(
            "auth.html",
            error=f"Facebook OAuth failed: {e}",
            tab="login",
            google_logo_b64=google_logo_b64,
            facebook_logo_b64=facebook_logo_b64,
        )
    return redirect(url_for("auth.login"))


@auth_bp.route("/oauth/callback")
def oauth_callback():
    """Handle OAuth callback from Supabase."""
    # Supabase handles the OAuth flow and redirects back with a token
    # Flask extracts the token and redirects to app
    token = request.args.get("token")

    if token:
        # Verify token and store in session
        user = supabase.auth.get_user(token)
        if user and user.user:
            session["supabase_token"] = token
            session["user_id"] = user.user.id
            session["email"] = user.user.email
            return redirect(f"/app?token={token}")

    return redirect(url_for("auth.login"))
