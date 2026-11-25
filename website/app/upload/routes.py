"""Upload proxy routes for forwarding documents to the FastAPI backend."""

import os
import requests
from flask import Blueprint, render_template, redirect, request, session, current_app

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")

# Backend API URL
_API_URL = os.environ.get("API_URL", "http://localhost:8000")
_CHAT_URL = os.environ.get("CHAT_EXTERNAL_URL", "http://localhost/chat")


@upload_bp.route("/", methods=["GET", "POST"])
def upload():
    """Handle document upload."""
    if request.method == "POST":
        # Check if user is authenticated
        token = session.get("supabase_token")
        user_id = session.get("user_id")

        if not token or not user_id:
            return redirect("/auth/login")

        # Check if file was provided
        if "document" not in request.files:
            return render_template(
                "upload.html",
                error="No file provided",
            )

        file = request.files["document"]
        if file.filename == "":
            return render_template(
                "upload.html",
                error="No file selected",
            )

        try:
            # Forward the file to the FastAPI backend
            files = {"file": (file.filename, file.stream, file.content_type)}
            headers = {"Authorization": f"Bearer {token}"}

            response = requests.post(
                f"{_API_URL}/api/upload",
                files=files,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            # Extract doc_id from response
            result = response.json()
            doc_id = result.get("doc_id")

            # Store doc_id in Redis for the chat service to retrieve
            if current_app.redis:
                current_app.redis.setex(
                    f"pending_doc:{user_id}",
                    300,  # 5 minute TTL
                    doc_id,
                )

            # Redirect to app with token
            return redirect(f"/app?token={token}")

        except requests.RequestException as e:
            return render_template(
                "upload.html",
                error=f"Upload failed: {str(e)}",
            )

    # GET request - render upload form
    return render_template("upload.html")
