# CloudGuard AI Platform

Production-ready security scanning platform with ML-powered risk assessment.

## Architecture

```
CloudGuardAI/
├── web/          # React frontend (Vite + MUI)
├── api/          # FastAPI backend service
├── ml/           # ML service (models + rules + LLM)
├── infra/        # Infrastructure (Docker, nginx)
└── legacy/       # Original Streamlit app (archived)
```

## Services

### API Service (`/api`)
- FastAPI REST API
- PostgreSQL database (scans, findings, feedback, model versions)
- Redis + RQ workers for async jobs
- Endpoints: `/scan`, `/feedback`, `/model/status`, `/retrain`

### ML Service (`/ml`)
- Core predictor (XGBoost + NN ensemble)
- Rules engine (YAML-based)
- LLM reasoner
- Risk aggregator
- Online learning with SGDClassifier
- Endpoints: `/predict`, `/rules-scan`, `/explain`, `/aggregate`

### Web UI (`/web`)
- React + Vite + Material-UI
- Pages: Scan, Results, Feedback, Model Status
- Axios API client

## Quick Start

### Development

```bash
# Start all services
cd infra
docker-compose up -d

# Access services
# Web UI: http://localhost:3000
# API: http://localhost:8000/docs
# ML Service: http://localhost:8001/docs
```

### API Development

```bash
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### ML Service Development

```bash
cd ml
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn ml_service.main:app --reload --port 8001
```

### Web Development

```bash
cd web
npm install
npm run dev
```

## Database Migrations

```bash
cd api
alembic upgrade head
```

## Running Tests

```bash
# API tests
cd api
pytest

# ML tests
cd ml
pytest

# Web tests
cd web
npm test
```

## CI/CD

GitHub Actions workflow automatically:
- Lints with black + flake8
- Runs unit tests
- Builds Docker images
- Pushes to registry (on main branch)

## Environment Variables

See `.env.example` files in each service directory.

## Production Deployment

1. Configure environment variables
2. Build images: `docker-compose build`
3. Deploy: `docker-compose up -d`
4. Run migrations: `docker-compose exec api alembic upgrade head`
5. Monitor logs: `docker-compose logs -f`

## License

See LICENSE file.
