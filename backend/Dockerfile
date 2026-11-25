# Dockerfile for LatMatrix Backend
# Multi-stage build for Python FastAPI application

# Stage 1: Builder stage
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements file
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

ENV PATH="/root/.local/bin:${PATH}"

# Download spaCy model during build
RUN python -m spacy download en_core_web_sm

# Stage 2: Runtime stage
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libxcb1 \
    libgl1 \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    SERVICE=api \
    PORT=8000 \
    PYTHONPATH=/app/src

# Create and set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy spaCy model data
COPY --from=builder /usr/local/lib/python3.12/site-packages /home/appuser/.local/lib/python3.12/site-packages

# Copy shared utilities
COPY shared/ ./shared/

# Copy application code
COPY backend/src/ ./src/

# Copy entrypoint script
COPY backend/docker-entrypoint.sh /app/docker-entrypoint.sh

# Convert line endings from CRLF to LF (Windows compatibility) and make executable
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check for FastAPI
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]