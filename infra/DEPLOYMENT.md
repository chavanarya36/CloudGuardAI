# CloudGuardAI Deployment Guide

## Table of Contents
- [Local Development with Docker Compose](#local-development-with-docker-compose)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Helm Chart Deployment](#helm-chart-deployment)
- [Production Checklist](#production-checklist)

---

## Local Development with Docker Compose

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/chavanarya36/CloudGuardAI.git
cd CloudGuardAI
```

2. **Create environment file**
```bash
cp infra/.env.example infra/.env
# Edit infra/.env with your configuration
```

3. **Build and start services**
```bash
cd infra
docker-compose up --build
```

4. **Access the application**
- Web UI: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ML Service: http://localhost:8001

5. **Run database migrations**
```bash
docker-compose exec api alembic upgrade head
```

### Useful Commands

**View logs**
```bash
docker-compose logs -f api
docker-compose logs -f ml-service
docker-compose logs -f worker
```

**Restart a service**
```bash
docker-compose restart api
```

**Stop all services**
```bash
docker-compose down
```

**Clean everything (including volumes)**
```bash
docker-compose down -v
```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster 1.24+
- kubectl configured
- nginx-ingress-controller installed
- cert-manager installed (for SSL)

### Deployment Steps

1. **Create namespace**
```bash
kubectl apply -f infra/k8s/namespace.yaml
```

2. **Deploy PostgreSQL**
```bash
kubectl apply -f infra/k8s/postgres.yaml
```

3. **Deploy Redis**
```bash
kubectl apply -f infra/k8s/redis.yaml
```

4. **Build and push Docker images**
```bash
# Build images
docker build -f infra/Dockerfile.api -t your-registry/cloudguard-api:latest .
docker build -f infra/Dockerfile.ml -t your-registry/cloudguard-ml:latest .
docker build -f infra/Dockerfile.web -t your-registry/cloudguard-web:latest .

# Push to registry
docker push your-registry/cloudguard-api:latest
docker push your-registry/cloudguard-ml:latest
docker push your-registry/cloudguard-web:latest
```

5. **Update image references in K8s manifests**
```bash
# Edit infra/k8s/api.yaml
# Edit infra/k8s/ml-service.yaml
# Edit infra/k8s/web.yaml
# Replace 'cloudguard/' with 'your-registry/cloudguard-'
```

6. **Deploy ML service**
```bash
kubectl apply -f infra/k8s/ml-service.yaml
```

7. **Deploy API**
```bash
kubectl apply -f infra/k8s/api.yaml
```

8. **Deploy workers**
```bash
kubectl apply -f infra/k8s/worker.yaml
```

9. **Deploy web UI**
```bash
kubectl apply -f infra/k8s/web.yaml
```

10. **Deploy ingress**
```bash
# First, update domain names in infra/k8s/ingress.yaml
kubectl apply -f infra/k8s/ingress.yaml
```

### Verify Deployment

```bash
# Check all pods
kubectl get pods -n cloudguard

# Check services
kubectl get svc -n cloudguard

# Check ingress
kubectl get ingress -n cloudguard

# View logs
kubectl logs -n cloudguard -l app=api
kubectl logs -n cloudguard -l app=ml-service
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment api -n cloudguard --replicas=5

# Autoscaling is configured via HPA
kubectl get hpa -n cloudguard
```

---

## Helm Chart Deployment

### Prerequisites
- Helm 3.0+
- Kubernetes cluster configured

### Quick Deploy

```bash
# Install chart
helm install cloudguard infra/helm/cloudguard \
  --namespace cloudguard \
  --create-namespace

# Upgrade deployment
helm upgrade cloudguard infra/helm/cloudguard \
  --namespace cloudguard

# Uninstall
helm uninstall cloudguard --namespace cloudguard
```

### Custom Values

Create `my-values.yaml`:
```yaml
replicaCount:
  api: 5
  ml: 3

ingress:
  hosts:
    - host: your-domain.com
      paths:
        - path: /
          pathType: Prefix
          backend: web

postgresql:
  auth:
    password: your-secure-password

config:
  secretKey: your-secret-key
```

Deploy with custom values:
```bash
helm install cloudguard infra/helm/cloudguard \
  --namespace cloudguard \
  --create-namespace \
  -f my-values.yaml
```

---

## Production Checklist

### Security
- [ ] Change default PostgreSQL password
- [ ] Set strong SECRET_KEY for JWT tokens
- [ ] Enable SSL/TLS via cert-manager
- [ ] Configure network policies
- [ ] Enable pod security policies
- [ ] Set up secrets management (Vault, Sealed Secrets)
- [ ] Configure RBAC properly
- [ ] Enable audit logging

### High Availability
- [ ] Deploy at least 3 API replicas
- [ ] Deploy at least 2 ML service replicas
- [ ] Configure pod anti-affinity rules
- [ ] Set up multi-zone deployment
- [ ] Configure persistent volume backups
- [ ] Set up database replication
- [ ] Configure Redis with sentinel/cluster mode

### Monitoring & Logging
- [ ] Deploy Prometheus for metrics
- [ ] Deploy Grafana dashboards
- [ ] Set up centralized logging (ELK/Loki)
- [ ] Configure alerting rules
- [ ] Monitor HPA metrics
- [ ] Track API latency and error rates
- [ ] Monitor ML model performance

### Performance
- [ ] Configure resource limits properly
- [ ] Enable horizontal pod autoscaling
- [ ] Set up Redis caching
- [ ] Configure connection pooling
- [ ] Optimize database queries
- [ ] Enable CDN for static assets
- [ ] Configure nginx caching

### Backup & Recovery
- [ ] Automated PostgreSQL backups (daily)
- [ ] Backup ML models and artifacts
- [ ] Test restore procedures
- [ ] Document disaster recovery plan
- [ ] Set up off-site backup storage

### CI/CD
- [ ] Set up GitHub Actions for automated builds
- [ ] Configure automated testing
- [ ] Set up staging environment
- [ ] Implement blue-green deployment
- [ ] Configure rollback procedures
- [ ] Set up canary deployments

---

## Troubleshooting

### Pods not starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n cloudguard

# Check logs
kubectl logs <pod-name> -n cloudguard

# Check events
kubectl get events -n cloudguard --sort-by='.lastTimestamp'
```

### Database connection issues
```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -n cloudguard -- \
  psql postgresql://cloudguard:cloudguard123@postgres:5432/cloudguard

# Check if migrations ran
kubectl exec -it deployment/api -n cloudguard -- alembic current
```

### Service unreachable
```bash
# Check service endpoints
kubectl get endpoints -n cloudguard

# Test internal connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n cloudguard -- \
  curl http://api:8000/health
```

---

## Environment Variables

### API Service
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ML_SERVICE_URL`: ML service URL
- `SECRET_KEY`: JWT secret key
- `ALLOWED_ORIGINS`: CORS allowed origins

### ML Service
- `ML_MODELS_PATH`: Path to model artifacts
- `RULES_PATH`: Path to rules engine
- `FEATURES_PATH`: Path to feature artifacts

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/chavanarya36/CloudGuardAI/issues
- Documentation: https://github.com/chavanarya36/CloudGuardAI/wiki
