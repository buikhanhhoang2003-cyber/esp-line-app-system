# docker/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Tokyo

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY esp-line-app-system/ ./esp-line-app-system/
COPY config/ ./config/
COPY models/ ./models/
COPY test/ ./test/

# Create non-root user
RUN useradd -m -u 1000 lineuser && chown -R lineuser:lineuser /app
USER lineuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "esp-line-app-system.services.api.line_app.endpoints:app", "--host", "0.0.0.0", "--port", "8000"]