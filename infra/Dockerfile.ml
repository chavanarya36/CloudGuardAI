FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ml/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy ML service code
COPY ml/ml_service ./ml_service
COPY ml/models ./models

# Copy rules engine (needed by integrated scanning)
COPY rules/rules_engine ./rules_engine

# Create directories for models and artifacts
RUN mkdir -p /app/models_artifacts /app/features_artifacts

# Copy AI model artifacts (use wildcard to avoid failure if specific files missing)
COPY ml/models_artifacts/ /app/models_artifacts/

# Set Python path for module imports
ENV PYTHONPATH=/app

# Add non-root user for security
RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Start server (exec form for proper signal handling)
CMD ["uvicorn", "ml_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
