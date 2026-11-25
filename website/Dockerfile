FROM python:3.12-slim

WORKDIR /app

# Install dependencies and curl for healthcheck
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy application source
COPY . .

# Expose Flask port
EXPOSE 5000

# Run with Gunicorn (4 sync workers)
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "app:create_app()"]
