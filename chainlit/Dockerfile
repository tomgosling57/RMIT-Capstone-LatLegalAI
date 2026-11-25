# Dockerfile for LatMatrix Chainlit Service
# Multi-stage build for Chainlit application

# Stage 1: Builder stage
FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies (including poppler-utils for pdf2image)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    poppler-utils \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    librsvg2-2 \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements file
COPY chainlit/requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Download spaCy model for NLP processing
RUN python -m spacy download en_core_web_sm

ENV PATH="/root/.local/bin:${PATH}"

# Stage 2: Runtime stage
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies (tesseract-ocr + poppler-utils for OCR PDF parsing)
RUN apt-get update && apt-get install -y \
    curl \
    libmagic1 \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    poppler-utils \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    librsvg2-2 \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    PYTHONPATH=/app \
    SERVICE=chainlit \
    CHAINLIT_PORT=8001 \
    API_BASE_URL=http://api:8000

# Create and set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy shared utilities
COPY shared/ ./shared/

# Copy application entry point (root-level, outside src/ package)
COPY chainlit/app.py ./app.py

# Copy application code
COPY chainlit/src/ ./src/

# Copy Chainlit configuration and theme assets
COPY chainlit/.chainlit/ ./.chainlit/
COPY chainlit/public/ ./public/

# Create data directory for SQLite database (must exist before volume mount)
RUN mkdir -p /app/data && chown appuser:appuser /app/data

# Copy entrypoint script
COPY chainlit/docker-entrypoint.sh /app/docker-entrypoint.sh

# Convert line endings from CRLF to LF (Windows compatibility) and make executable
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

# Create data directory for SQLite database persistence
RUN mkdir -p /app/data

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose Chainlit port
EXPOSE 8001

# Run the entrypoint script
CMD ["/app/docker-entrypoint.sh"]
