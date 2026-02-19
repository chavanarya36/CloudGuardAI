# CloudGuard AI - Quick Deployment Reference

## 🚀 Quick Commands

### Docker Deployment (Recommended)
```powershell
# Start all services
docker compose -f infra/docker-compose.yml up -d

# View logs
docker compose -f infra/docker-compose.yml logs -f

# Stop services
docker compose -f infra/docker-compose.yml down

# Rebuild after changes
docker compose -f infra/docker-compose.yml up -d --build
```

### Local Development (No Docker)
```powershell
# Full setup
.\start.ps1 -InstallDeps -RunTests

# Quick start
.\start.ps1
```

### Legacy Startup
```powershell
.\startup.bat
```

---

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Web UI** | http://localhost:3000 | Main application interface |
| **API Docs** | http://localhost:8000/docs | FastAPI Swagger documentation |
| **API Health** | http://localhost:8000/health | API health check |
| **ML Service** | http://localhost:8001/health | ML service health check |
| **PostgreSQL** | localhost:5432 | Database (cloudguard/cloudguard) |
| **Redis** | localhost:6379 | Cache and job queue |

---

## 📦 What's Deployed

### Container Services
1. **postgres** - PostgreSQL database
2. **redis** - Cache and job queue
3. **ml-service** - AI models (GNN, RL, Transformer) + Traditional ML
4. **api** - FastAPI backend with scanners
5. **worker** - Background job processing
6. **web** - React frontend (if using full stack)

### AI Models Included
- ✅ `gnn_attack_detector.pt` (114K params)
- ✅ `rl_auto_fix_agent.pt` (31K params)
- ✅ Transformer implementation (4.9M params)
- ✅ Traditional ML models (ensemble, etc.)

---

## 🧪 Quick Tests

### Test AI Models
```powershell
# Verify all AI implementations
python verify_ai_implementations.py
```

### Test API Endpoints
```powershell
# Health check
curl http://localhost:8000/health

# GNN endpoint (example)
curl -X POST http://localhost:8000/api/scan/gnn `
  -H "Content-Type: application/json" `
  -Body '{"code": "resource \"aws_s3_bucket\" { acl = \"public-read\" }"}'
```

### Test ML Service
```powershell
curl http://localhost:8001/health
```

---

## 🔧 Troubleshooting

### Services won't start
```powershell
# Check Docker is running
docker ps

# View service logs
docker compose -f infra/docker-compose.yml logs api
docker compose -f infra/docker-compose.yml logs ml-service

# Restart specific service
docker compose -f infra/docker-compose.yml restart api
```

### Port already in use
```powershell
# Find process using port
netstat -ano | findstr ":8000"
netstat -ano | findstr ":8001"

# Kill process
taskkill /PID <PID> /F
```

### AI models not loading
```powershell
# Check models in container
docker compose -f infra/docker-compose.yml exec ml-service ls -la /app/models_artifacts/

# Should show:
# - gnn_attack_detector.pt
# - rl_auto_fix_agent.pt
# - *.joblib files
```

### Database issues
```powershell
# Run migrations
docker compose -f infra/docker-compose.yml exec api alembic upgrade head

# Reset database
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up -d
```

---

## 📊 Monitoring

### View Logs
```powershell
# All services
docker compose -f infra/docker-compose.yml logs -f

# Specific service
docker compose -f infra/docker-compose.yml logs -f api
docker compose -f infra/docker-compose.yml logs -f ml-service
docker compose -f infra/docker-compose.yml logs -f worker
```

### Check Resource Usage
```powershell
# Container stats
docker stats

# Service status
docker compose -f infra/docker-compose.yml ps
```

### Check AI Performance
```powershell
# ML service metrics (if implemented)
curl http://localhost:8001/metrics

# Expected metrics:
# - GNN inference time: <500ms
# - RL decision time: <100ms
# - Transformer generation: 1-3s
```

---

## 🔄 Updates & Maintenance

### Update AI Models
```powershell
# Copy new models to artifacts directory
cp new_model.pt ml/models_artifacts/

# Rebuild ML service
docker compose -f infra/docker-compose.yml up -d --build ml-service
```

### Update Code
```powershell
# Pull latest changes
git pull

# Rebuild and restart
docker compose -f infra/docker-compose.yml up -d --build
```

### Backup Database
```powershell
# Create backup
docker compose -f infra/docker-compose.yml exec postgres pg_dump -U cloudguard cloudguard > backup.sql

# Restore backup
docker compose -f infra/docker-compose.yml exec -T postgres psql -U cloudguard cloudguard < backup.sql
```

---

## 🚢 Production Checklist

Before deploying to production:

- [ ] Update SECRET_KEY in `.env`
- [ ] Change database password
- [ ] Configure SSL/TLS certificates
- [ ] Setup authentication/authorization
- [ ] Enable monitoring (Prometheus, Grafana)
- [ ] Configure log aggregation
- [ ] Setup automated backups
- [ ] Review security settings
- [ ] Load test AI endpoints
- [ ] Configure rate limiting
- [ ] Setup alerts and notifications

---

## 📖 Full Documentation

For complete deployment instructions, see:
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Detailed deployment guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[README.md](README.md)** - Project overview

---

## 🆘 Support

**Issues:**
- Check logs: `docker compose logs -f`
- Verify models: `python verify_ai_implementations.py`
- Check health: `curl http://localhost:8000/health`

**Documentation:**
- API Docs: http://localhost:8000/docs
- Architecture: docs/ARCHITECTURE.md
- Phase 7 Results: PHASE_7_COMPLETE.md

**Quick Reset:**
```powershell
# Nuclear option - clean everything and restart
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up -d --build
```

---

## ✅ Success Indicators

Your deployment is successful if:

1. ✅ All containers are running: `docker compose ps`
2. ✅ Web UI accessible: http://localhost:3000
3. ✅ API health check passes: http://localhost:8000/health
4. ✅ ML service responds: http://localhost:8001/health
5. ✅ Can upload and scan a file
6. ✅ GNN detection works
7. ✅ RL suggestions appear
8. ✅ No errors in logs

---

**Ready to scan! 🛡️**
