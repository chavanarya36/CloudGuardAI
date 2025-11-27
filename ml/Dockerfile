FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY ../models_artifacts /app/models_artifacts
COPY ../rules_engine /app/rules_engine
COPY ../features_artifacts /app/features_artifacts
EXPOSE 8001
CMD ["uvicorn", "ml_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
