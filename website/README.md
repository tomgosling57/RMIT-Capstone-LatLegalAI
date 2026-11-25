# Website Service

Flask web application for the LatMatrix Legal Simplifier. This service handles all user-facing pages, authentication, and the document upload form. It is the primary entry point for users visiting the application.

---

# Website Service

Flask-based web application providing public-facing pages, authentication, and document upload proxy for the LatMatrix Legal Simplifier application.

## Overview

The Website Service is the public-facing entry point for the LatMatrix application. It provides:

- **Public Pages**: Home, pricing, and informational pages
- **Authentication**: User login, signup, and OAuth integration via Supabase
- **Document Upload Proxy**: Secure document upload with authentication
- **Rate Limiting & Security**: Protection against abuse and attacks

## Project Structure

```
website/
├── app/
│   ├── __init__.py              # Application factory
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py            # Login, signup, OAuth routes
│   │   └── supabase_client.py   # Supabase client configuration
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py            # Home, pricing routes
│   ├── upload/
│   │   ├── __init__.py
│   │   └── routes.py            # Document upload proxy
│   ├── static/
│   │   ├── FacebookLogo.png
│   │   ├── GoogleLogo.png
│   │   ├── htmx.min.js
│   │   ├── logo.png
│   │   └── theme.css
│   ├── templates/
│   |   ├── _pricing_grid.html
│   |   ├── auth.html
│   |   ├── base.html
│   |   ├── home.html
│   |   └── pricing.html
│   └── __init__.py
├── config.py                    # Configuration file
├── Dockerfile                   # Container definition
├── requirements.txt             # Python dependencies
└── README.md
```

---

## Technology Stack

| Component | Technology | Version |
|---|---|---|
| **Framework** | [Flask](https://flask.palletsprojects.com) | 3.0.3 |
| **Language** | Python | 3.12 |
| **WSGI Server** | Gunicorn | 22.0.0 |
| **Authentication** | Supabase (via `supabase` client) | 2.5.0 |
| **Rate Limiting** | Flask-Limiter (Redis-backed) | 3.8.0 |
| **Security Headers** | Flask-Talisman | 1.1.0 |
| **HTTP Client** | requests | 2.32.3 |
| **Session Store / Rate Limit Backend** | Redis | 5.0.7 (client) |
| **Container** | Docker | — |

---

## Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

No additional system dependencies are required beyond those managed by Docker.

---

## Environment Variables

Set these in the project root `.env` file (copied from [`env.example`](../env.example)).

### Required

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask secret key used for session encryption. Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SUPABASE_URL` | Supabase project URL (used for authentication) |
| `SUPABASE_KEY` | Supabase anon/public API key |

### Optional

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | `production` | Set to `development` for debug mode and detailed error pages |
| `API_URL` | `http://api:8000` | Backend FastAPI service URL. Use `http://localhost:8000` for local dev |
| `CHAT_EXTERNAL_URL` | `http://localhost/chat` | External URL for the Chainlit service (used for post-login redirects) |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `RATELIMIT_STORAGE_URI` | `redis://redis:6379/2` | Redis URI for Flask-Limiter (uses Redis db=2) |

---

## Running the Service

### Using Docker (recommended)

```bash
# From the project root
docker compose up website
```

The service is available at http://localhost:5000 directly, or at http://localhost via the Nginx reverse proxy.

### Local development

```bash
cd website
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run --host 0.0.0.0 --port 5000
```

---

## Project Structure

```
website/
├── app/                    # Flask application package
├── config.py               # Flask configuration
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Testing

See the [Frontend Testing README](../tests/frontend/README.md) for setup and instructions on running the test suite for this service.