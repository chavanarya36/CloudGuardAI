<p align="center">
  <h1 align="center">🛡️ CloudGuardAI</h1>
  <p align="center">
    <strong>AI-Powered Infrastructure as Code Security Scanner</strong><br>
    <em>3 Novel ML Models · GNN Attack Paths · RL Auto-Remediation · Transformer Code Gen</em>
  </p>
  <p align="center">
    <a href="https://github.com/chavanarya36/CloudGuardAI/actions"><img src="https://img.shields.io/github/actions/workflow/status/chavanarya36/CloudGuardAI/pipeline.yml?branch=main&label=CI%2FCD&logo=github" alt="CI/CD"></a>
    <img src="https://img.shields.io/badge/tests-388%20passing-brightgreen?logo=pytest" alt="Tests">
    <img src="https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/react-18.2-61DAFB?logo=react&logoColor=black" alt="React">
    <img src="https://img.shields.io/badge/AI_contribution-80%25-blueviolet" alt="AI 80%">
    <a href="docs/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  </p>
</p>

---

CloudGuardAI is a full-stack security scanning platform that uses **3 novel AI models** (GNN + RL + Transformer) alongside traditional tools to detect and auto-remediate vulnerabilities in Infrastructure as Code files. Built with FastAPI, React 18, PyTorch, and deployed via Docker/Kubernetes.

## ✨ Key Highlights

| Capability | Details |
|:-----------|:--------|
| 🧠 **GNN Attack Paths** | Graph Neural Network (114K params) detects multi-hop attack chains across infrastructure |
| 🎯 **RL Auto-Fix** | Deep Q-Network (31K params) selects optimal remediation from 15 action strategies |
| ✨ **Transformer Code Gen** | 2-layer encoder (~150K params) generates secure IaC replacements |
| 🔁 **Adaptive Learning** | 8-subsystem self-improving engine — drift detection, pattern discovery, auto-retrain |
| 🔐 **Production Security** | JWT + API-key auth, rate limiting, Prometheus metrics, 3-tier Docker network isolation |
| 📊 **388 Tests Passing** | Unit, integration, API, ML — zero failures |

## 🏗️ Architecture

```
┌───────────────┐       ┌───────────────────┐       ┌───────────────────────────┐
│  React 18 UI  │──────▶│  FastAPI Backend   │──────▶│      ML Service           │
│  (Vite + MUI) │  HTTP │  25 routes · JWT   │  HTTP │  🧠 GNN  (114K params)   │
│  10 pages     │◀──────│  Rate Limit · CORS │◀──────│  🎯 RL   (31K params)    │
└───────────────┘       └────────┬──────────┘       │  ✨ Transformer (~150K)   │
                                 │                   │  📦 Ensemble (13MB)       │
                      ┌──────────┴──────────┐       └───────────────────────────┘
                      │                     │
               ┌──────┴──────┐    ┌─────────┴─────────┐
               │ PostgreSQL  │    │   Redis + Workers  │
               │ (SQLite dev)│    │   Background Jobs  │
               └─────────────┘    └───────────────────┘
```

**Detailed architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/chavanarya36/CloudGuardAI.git
cd CloudGuardAI
docker compose -f infra/docker-compose.yml up -d
```

| Service | URL |
|---------|-----|
| Web UI | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| ML Service | http://localhost:8001/docs |

### Option 2: Local Development

```powershell
# Install dependencies
pip install -r api/requirements.txt
pip install -r ml/requirements.txt
cd web && npm install && cd ..

# Start all services
.\startup.bat              # Windows — starts API + ML + Web
# OR
.\start.ps1 -InstallDeps   # PowerShell with options
```

### Manual Start (3 terminals)

```bash
# Terminal 1 — API (port 8000)
cd api && set PYTHONPATH=%CD% && python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — ML Service (port 8001)
cd ml && set PYTHONPATH=%CD% && python -m uvicorn ml_service.main:app --reload --port 8001

# Terminal 3 — Web UI (port 3000)
cd web && npm run dev
```

## 📖 Usage

1. **Navigate** to http://localhost:3000
2. **Upload** a Terraform (`.tf`), Kubernetes (`.yaml`), or CloudFormation (`.json`) file
3. **Select scan mode** — All (full AI pipeline), GNN, or Checkov
4. **Review findings** with severity levels, GNN attack paths, RL fix recommendations, and generated secure code

## 📁 Project Structure

```
CloudGuardAI/
├── api/                    # FastAPI backend — 25 routes, JWT auth, rate limiting
│   ├── app/                # Core: main.py, models.py, schemas.py, auth.py, config.py
│   ├── scanners/           # CVE, secrets, compliance, GNN, integrated scanner
│   └── tests/              # 20 API integration tests
├── ml/                     # ML service — GNN, RL, Transformer, ensemble
│   ├── ml_service/         # FastAPI endpoints: predict, rules-scan, aggregate, train
│   ├── models/             # rl_auto_fix.py, graph_neural_network.py, transformer
│   ├── models_artifacts/   # Trained model weights (.pt, .joblib)
│   └── tests/              # 5 ML service tests
├── web/                    # React 18 + Vite + MUI + Tailwind
│   └── src/pages/          # Scan, Dashboard, Results, Learning, Settings, etc.
├── rules/                  # YAML-based rules engine (5 matcher types)
├── tests/                  # 388 unit/integration/validation tests
├── infra/                  # Docker Compose, Helm chart, k8s manifests, CI/CD
├── scripts/                # Data prep, training, testing, validation utilities
└── docs/                   # Architecture, phase reports, deployment guides
```

## 🧪 Testing

```bash
# Run all tests with one command (388 total)
python -m pytest                            # 388 passed, 10 skipped

# Or run individual suites
python -m pytest tests/ -q                  # 388 passed, 10 skipped
python -m pytest api/tests/ -q              # 20 passed
python -m pytest ml/tests/ -q               # 5 passed

# Run specific suites
python -m pytest tests/unit/ -v             # Unit tests
python -m pytest tests/integration/ -v      # Integration tests
python -m pytest tests/validation/ -v       # Validation tests
```

## 📊 AI Model Performance

| Model | Parameters | Training Data | Key Metric | Inference |
|-------|-----------|---------------|--------|-----------|
| **GNN Attack Detector** | 114,434 | Synthetic graphs (400 train / 100 val) | See [evaluation report](docs/MODEL_EVALUATION.md) | <500ms |
| **RL Auto-Fix Agent** | 31,503 | Simulated vulnerability episodes | See [evaluation report](docs/MODEL_EVALUATION.md) | <100ms |
| **Transformer Code Gen** | ~150K | ~30 synthetic IaC pairs | See [evaluation report](docs/MODEL_EVALUATION.md) | <1s |
| **Ensemble Classifier** | ~13MB | 21K IaC files | 70% baseline | <50ms |

> **⚠️ Limitations:** All novel ML models (GNN, RL, Transformer) are trained on **synthetic data** as a proof-of-concept. Reported metrics reflect performance on synthetic test sets and should not be extrapolated to production accuracy. See [docs/MODEL_EVALUATION.md](docs/MODEL_EVALUATION.md) for full transparent evaluation with caveats.

## 🔐 Security Features

- **Authentication:** JWT tokens + API key auth with dev bypass mode
- **Rate Limiting:** Token bucket — 2/s scan, 5/s auth, 10/s general
- **Observability:** Prometheus metrics, request tracing, timing middleware
- **Docker Hardening:** 3-tier network isolation, resource limits, `no-new-privileges`, read-only FS
- **Helm:** HPA (2-10 replicas), PDB, NetworkPolicy (4 policies), StatefulSet for Postgres

## 🔁 Adaptive Learning Engine

Self-improving pipeline with 8 subsystems:

| Subsystem | Purpose |
|-----------|---------|
| RichFeatureExtractor | 40-dimension feature vectors (structural, credential, network, crypto, IAM, logging) |
| DriftDetector | PSI-based drift detection → auto-retrain trigger |
| AdaptiveRuleWeights | Per-rule Bayesian confidence (TP/FP tracking with Laplace prior) |
| PatternDiscoveryEngine | Clusters findings → auto-generates YAML rules |
| ModelEvaluator | Champion/challenger with ≥2% F1 improvement gate |
| LearningTelemetry | Full audit trail (last 1000 events) |

**6 REST endpoints** at `/learning/*` — status, patterns, drift, rule-weights, telemetry, discover.

## 🚢 Deployment

```bash
# Docker Compose (local)
docker compose -f infra/docker-compose.yml up -d

# Kubernetes with Helm
helm install cloudguard infra/helm/cloudguard/

# Direct k8s manifests
kubectl apply -f infra/k8s/
```

See [infra/README.md](infra/README.md) for full deployment guide.

## 🎯 Novel Academic Contributions

1. **GNN for IaC Attack Paths** — First application of Graph Attention Networks to multi-hop attack detection in infrastructure code
2. **RL for Auto-Remediation** — First Deep Q-Network agent for automatic vulnerability fixing with 15 learned strategies
3. **Transformer for Secure Code** — First attention-based transformer for security-focused IaC code generation

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full system architecture and data flow |
| [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) | Complete project overview |
| [docs/PHASE_7.1_GNN_IMPLEMENTATION.md](docs/PHASE_7.1_GNN_IMPLEMENTATION.md) | GNN implementation details |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Contribution guidelines |
| [docs/MODEL_EVALUATION.md](docs/MODEL_EVALUATION.md) | Honest ML model evaluation with metrics and caveats |
| [REVIEW_3_READINESS.md](REVIEW_3_READINESS.md) | Review readiness report |

## 🤝 Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License — see [docs/LICENSE](docs/LICENSE)

## 📞 Contact

**Author:** [@chavanarya36](https://github.com/chavanarya36)  
**Repository:** [github.com/chavanarya36/CloudGuardAI](https://github.com/chavanarya36/CloudGuardAI)

---

<p align="center"><strong>Secure your cloud infrastructure with AI-powered insights</strong> 🛡️</p>
