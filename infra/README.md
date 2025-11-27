# CloudGuard AI Infrastructure

Docker-based infrastructure for the CloudGuard AI platform.

## Services

- **postgres**: PostgreSQL 15 database
- **redis**: Redis for job queuing
- **ml-service**: ML inference service (port 8001)
- **api**: FastAPI backend (port 8000)
- **worker**: RQ worker for async jobs
- **web**: React frontend with nginx (port 3000)

## Quick Start

1. Copy environment file:
```bash
cp .env.example .env
```

2. Update environment variables in `.env` (especially API keys)

3. Start all services:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
docker-compose exec api alembic upgrade head
```

5. Access services:
- Web UI: http://localhost:3000
- API Docs: http://localhost:8000/docs
- ML Service Docs: http://localhost:8001/docs

## Development

### Start services for development:
```bash
docker-compose up postgres redis ml-service
```

Then run API and Web locally for faster iteration.

### View logs:
```bash
docker-compose logs -f [service-name]
```

### Restart a service:
```bash
docker-compose restart [service-name]
```

### Stop all services:
```bash
docker-compose down
```

### Rebuild images:
```bash
docker-compose build
```

## Production Deployment

1. Update environment variables for production
2. Set strong passwords and secret keys
3. Configure SSL/TLS certificates
4. Use external managed database and Redis
5. Scale workers as needed:
```bash
docker-compose up -d --scale worker=3
```

## Monitoring

View service health:
```bash
docker-compose ps
```

Check resource usage:
```bash
docker stats
```

## Troubleshooting

### Database connection issues:
```bash
docker-compose logs postgres
docker-compose exec postgres psql -U cloudguard -d cloudguard
```

### Redis connection issues:
```bash
docker-compose logs redis
docker-compose exec redis redis-cli ping
```

### Worker not processing jobs:
```bash
docker-compose logs worker
docker-compose restart worker
```
