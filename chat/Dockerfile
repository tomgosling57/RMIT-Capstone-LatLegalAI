# Dockerfile for LatMatrix Frontend
# Multi-stage build for Streamlit application

# Stage 1: Builder stage
FROM python:3.12-slim as builder

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
COPY chat/requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

ENV PATH="/root/.local/bin:${PATH}"

# Stage 2: Runtime stage
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    SERVICE=frontend \
    PORT=8501 \
    API_URL=http://api:8000

# Create and set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY chat/src/ ./src/

# Copy Streamlit configuration
COPY chat/.streamlit/ .streamlit/

# Copy entrypoint script
COPY chat/docker-entrypoint.sh /app/docker-entrypoint.sh

# Convert line endings from CRLF to LF (Windows compatibility) and make executable
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Run the entrypoint script
CMD ["/app/docker-entrypoint.sh"]