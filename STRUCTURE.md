# CloudGuard AI - Project Structure

This document describes the clean, organized folder structure of CloudGuardAI.

## 📁 Root Directory Structure

```
CloudGuardAI/
├── 📄 README.md                    # Main project documentation
├── 📄 start.ps1                    # Quick start script (Windows)
├── 📄 startup.bat                  # Alternative startup script
├── 📄 .gitignore                   # Git ignore rules
│
├── 📂 api/                         # FastAPI Backend Service
│   ├── app/                        # Application code
│   │   ├── main.py                 # API entry point
│   │   ├── config.py               # Configuration
│   │   ├── database.py             # Database connection
│   │   ├── models.py               # Data models
│   │   └── ...
│   ├── scanners/                   # Security scanners
│   │   ├── integrated_scanner.py   # Main scanner orchestrator
│   │   ├── gnn_scanner.py          # Graph Neural Network scanner
│   │   ├── secrets_scanner.py      # Secrets detection
│   │   ├── cve_scanner.py          # CVE vulnerability scanner
│   │   └── compliance_scanner.py   # Compliance checks
│   ├── alembic/                    # Database migrations
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # Container image
│   └── .env                        # Environment variables
│
├── 📂 ml/                          # Machine Learning Service
│   ├── ml_service/                 # ML API service
│   │   ├── main.py                 # ML service entry point
│   │   ├── trainer.py              # Online training
│   │   └── ...
│   ├── models/                     # AI model implementations
│   │   ├── graph_neural_network.py # GNN model (114K params)
│   │   ├── rl_auto_fix.py          # RL agent (31K params)
│   │   ├── transformer_code_gen.py # Transformer (4.9M params)
│   │   ├── train_gnn.py            # GNN training script
│   │   └── ...
│   ├── models_artifacts/           # Trained model files
│   │   ├── gnn_attack_detector.pt  # Trained GNN model
│   │   ├── rl_auto_fix_agent.pt    # Trained RL agent
│   │   ├── best_model_ensemble.joblib
│   │   └── ...
│   ├── features_artifacts/         # Feature engineering data
│   ├── requirements.txt            # Python dependencies
│   └── .env                        # Environment variables
│
├── 📂 web/                         # React Frontend
│   ├── src/                        # React components
│   │   ├── main.jsx                # App entry point
│   │   ├── components/             # UI components
│   │   └── ...
│   ├── public/                     # Static assets
│   ├── package.json                # Node dependencies
│   ├── vite.config.js              # Vite configuration
│   └── Dockerfile                  # Container image
│
├── 📂 docs/                        # Documentation
│   ├── README.md                   # Documentation index
│   ├── ARCHITECTURE.md             # System architecture
│   ├── PROJECT_SUMMARY.md          # Academic project summary
│   ├── PROJECT_STATUS.md           # Current status
│   ├── FINAL_RESULTS_SUMMARY.md    # Validation results
│   ├── presentations/              # Presentation materials
│   │   ├── INDUSTRY_PROJECT_PRESENTATION.md
│   │   ├── INTERVIEW_GUIDE.md
│   │   └── THESIS_DEFENSE_SUMMARY.md
│   ├── phases/                     # Development phases
│   │   ├── PHASE_1_COMPLETION_REPORT.md
│   │   ├── PHASE_7.1_GNN_IMPLEMENTATION.md
│   │   └── ...
│   └── deployment/                 # Deployment guides
│
├── 📂 infra/                       # Infrastructure & Deployment
│   ├── docker-compose.yml          # Multi-container setup
│   ├── Dockerfile.api              # API container
│   ├── Dockerfile.ml               # ML service container
│   ├── Dockerfile.web              # Web container
│   ├── nginx.conf                  # Reverse proxy config
│   ├── deploy.ps1                  # Deployment script
│   ├── k8s/                        # Kubernetes manifests
│   │   ├── api-deployment.yaml
│   │   ├── ml-deployment.yaml
│   │   └── ...
│   └── helm/                       # Helm charts
│       └── cloudguard/
│
├── 📂 tests/                       # Test Suite
│   ├── conftest.py                 # Test configuration
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   ├── validation/                 # Validation tests
│   │   ├── full_scan_ml_rules.py   # Full workspace scan
│   │   └── ...
│   ├── ml/                         # ML model tests
│   └── analysis/                   # Analysis scripts
│
├── 📂 scripts/                     # Utility Scripts
│   ├── data_prep/                  # Data preparation
│   ├── training/                   # Model training scripts
│   ├── testing/                    # Testing utilities
│   └── validation/                 # Validation scripts
│
├── 📂 data/                        # Data Directory
│   ├── datasets/                   # Training datasets
│   ├── samples/                    # Sample IaC files
│   ├── merged_findings_v2/         # Findings data
│   └── labels_artifacts/           # Labeled data
│
├── 📂 rules/                       # Security Rules
│   └── rules_engine/               # Custom security rules
│
└── 📂 .archive/                    # Archived Files (gitignored)
    ├── scan_progress.log           # Old logs
    ├── test_working.py             # Temporary test files
    └── ...
```

## 🎯 Key Directories Explained

### `/api` - Backend API Service
The FastAPI-based backend that orchestrates all security scanners and provides RESTful API.

**Key Files:**
- `app/main.py` - API endpoints and routing
- `scanners/integrated_scanner.py` - Main scanning orchestrator
- `scanners/gnn_scanner.py` - Novel GNN attack path detector

### `/ml` - Machine Learning Service
Standalone FastAPI service for AI model inference and training.

**Key Files:**
- `models/graph_neural_network.py` - GNN implementation (114K params)
- `models/rl_auto_fix.py` - Reinforcement learning agent
- `models/transformer_code_gen.py` - Code generation model
- `models_artifacts/` - Trained model weights

### `/web` - Frontend Application
React-based web interface for uploading files and viewing scan results.

**Key Files:**
- `src/main.jsx` - Application entry point
- `src/components/` - Reusable UI components

### `/docs` - Documentation
All project documentation, presentations, and reports.

**Sub-directories:**
- `presentations/` - Interview guides, defense materials
- `phases/` - Development phase reports
- `deployment/` - Deployment documentation

### `/infra` - Infrastructure
Container orchestration, Kubernetes manifests, and deployment configurations.

**Key Files:**
- `docker-compose.yml` - Local development setup
- `k8s/` - Production Kubernetes deployment
- `helm/` - Helm chart for cloud deployment

### `/tests` - Test Suite
Comprehensive testing including unit, integration, and validation tests.

### `/.archive` - Temporary/Old Files
Archived temporary files, logs, and old versions (excluded from Git).

## 🚀 Quick Navigation

### For Development:
- Start here: `README.md`
- API development: `api/app/main.py`
- ML models: `ml/models/`
- Frontend: `web/src/`

### For Documentation:
- Architecture: `docs/ARCHITECTURE.md`
- Project summary: `docs/PROJECT_SUMMARY.md`
- Interview prep: `docs/presentations/INTERVIEW_GUIDE.md`

### For Deployment:
- Docker: `infra/docker-compose.yml`
- Kubernetes: `infra/k8s/`
- Scripts: `start.ps1` or `startup.bat`

### For Testing:
- Run tests: `tests/`
- Validation: `tests/validation/full_scan_ml_rules.py`

## 📋 File Naming Conventions

- **Python files**: `snake_case.py`
- **React components**: `PascalCase.jsx`
- **Configuration**: `lowercase.config.js`
- **Documentation**: `UPPERCASE_WITH_UNDERSCORES.md`
- **Scripts**: `lowercase_with_underscores.ps1`

## 🧹 Cleanup Guidelines

**Archived files** (in `.archive/`):
- Temporary test scripts
- Old log files
- Experimental code
- One-off utility scripts

**Not tracked in Git**:
- `__pycache__/` directories
- `.env` files (use `.env.example` as template)
- `node_modules/`
- Trained models (tracked with Git LFS)
- Build artifacts

## 🔄 Maintenance

To keep the project clean:
1. Move temporary files to `.archive/`
2. Update `.gitignore` for new file types
3. Document new directories in this file
4. Remove unused dependencies from `requirements.txt`/`package.json`
5. Archive old experiment code

---

**Last Updated:** February 3, 2026  
**Maintained by:** CloudGuard AI Team
