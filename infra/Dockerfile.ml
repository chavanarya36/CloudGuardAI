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

# Copy CloudGuard modules (needed by ML service)
COPY cloudguard ./cloudguard
COPY rules_engine ./rules_engine
COPY pipeline ./pipeline
COPY llm_reasoner.py .
COPY risk_aggregator.py .

# Create directories for models and artifacts
RUN mkdir -p /app/models_artifacts /app/features_artifacts

# Expose port
EXPOSE 8001

# Start server
CMD ["uvicorn", "ml_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
