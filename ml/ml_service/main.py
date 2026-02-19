import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

# Add parent directory to path to import existing CloudGuard modules
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, HTTPException
from .config import settings
from .schemas import (
    PredictRequest, PredictResponse,
    RulesScanRequest, RulesScanResponse,
    ExplainRequest, ExplainResponse,
    AggregateRequest, AggregateResponse,
    OnlineTrainRequest, OnlineTrainResponse,
    Finding, ExplainedFinding
)
from .observability import RequestIDMiddleware, TimingMiddleware, OperationTimer

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model cache — loaded once at startup, reused across requests
# ---------------------------------------------------------------------------
_model_cache: dict = {"ensemble": None, "loaded": False}


def _load_models():
    """Pre-load ML model on startup so /predict doesn't reload every request."""
    try:
        import joblib
        model_path = Path(__file__).parent.parent / "models_artifacts" / "best_model_ensemble.joblib"
        if model_path.exists():
            _model_cache["ensemble"] = joblib.load(model_path)
            _model_cache["loaded"] = True
            logger.info("Ensemble model loaded from %s", model_path)
        else:
            logger.warning("Model file not found at %s — will use heuristic fallback", model_path)
    except Exception as exc:
        logger.error("Failed to load ensemble model: %s", exc)


@asynccontextmanager
async def lifespan(app):
    """Modern lifespan handler — replaces deprecated @app.on_event('startup')."""
    _load_models()
    yield


app = FastAPI(
    title="CloudGuard ML Service",
    description="ML service for security scanning with models, rules engine, and LLM reasoning",
    version="1.0.0",
    lifespan=lifespan,
)

# Add observability middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)


@app.get("/")
async def root():
    """Service information endpoint — returns name, version, and status."""
    return {
        "service": "CloudGuard ML Service",
        "version": app.version,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Liveness probe — returns 200 if the service is running."""
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Get ML prediction for a file using the ensemble model.
    Uses the pre-loaded model from _model_cache (loaded at startup).
    Feature extraction is aligned with trainer.py (40-dim rich features).
    """
    try:
        content_lower = request.file_content.lower()
        confidence = 0.0  # will be derived from actual model output

        model = _model_cache.get("ensemble")

        if model is None:
            # ── Heuristic fallback (no model on disk) ─────────────────
            risk_indicators = [
                'public', '0.0.0.0/0', 'acl', 'versioning = false',
                'encryption', 'password', 'secret', 'key', 'security_group',
                'ingress', 'egress', 'cidr_block', 'publicly_accessible'
            ]
            matches = sum(1 for ind in risk_indicators if ind in content_lower)
            score = min(0.3 + (matches * 0.10), 1.0)
            confidence = 0.40  # low confidence — heuristic only
            model_used = "heuristic"
        else:
            # ── Model-based prediction ────────────────────────────────
            # Try 40-dim rich features first (aligned with trainer.py)
            try:
                feature_vector = _extract_rich_features(request.file_content, request.file_path)
                feature_array = [feature_vector]

                try:
                    prediction_proba = model.predict_proba(feature_array)[0]
                    score = float(prediction_proba[1]) if len(prediction_proba) > 1 else float(prediction_proba[0])
                    confidence = float(max(prediction_proba))  # actual model confidence
                except Exception:
                    score = float(model.predict(feature_array)[0])
                    confidence = 0.6
                model_used = "ensemble_40dim"
            except Exception as dim_err:
                # Dimension mismatch — fall back to 8-feature simple extraction
                logger.warning("40-dim features failed (%s), falling back to 8-dim", dim_err)
                features_simple = {
                    'public_count': content_lower.count('public'),
                    'open_cidr': content_lower.count('0.0.0.0/0'),
                    'security_group': content_lower.count('security_group'),
                    'encryption': content_lower.count('encryption'),
                    'versioning': content_lower.count('versioning'),
                    'password': content_lower.count('password'),
                    'secret': content_lower.count('secret'),
                    'file_length': len(request.file_content),
                }
                feature_vector = [list(features_simple.values())]
                try:
                    prediction_proba = model.predict_proba(feature_vector)[0]
                    score = float(prediction_proba[1]) if len(prediction_proba) > 1 else float(prediction_proba[0])
                    confidence = float(max(prediction_proba))
                except Exception:
                    score = float(model.predict(feature_vector)[0])
                    confidence = 0.55
                model_used = "ensemble_8dim"

        # Map score to category
        if score >= 0.8:
            prediction = 'critical'
        elif score >= 0.6:
            prediction = 'high'
        elif score >= 0.4:
            prediction = 'medium'
        else:
            prediction = 'low'

        return PredictResponse(
            risk_score=round(float(score), 4),
            confidence=round(confidence, 4),
            prediction=prediction,
            features={"ml_model": model_used, "analyzed": True}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


def _extract_rich_features(content: str, filename: str = "") -> list:
    """40-dim rich feature vector — mirrors trainer.py / adaptive_learning.py."""
    import re
    lower = content.lower()
    lines = content.split("\n")
    feats: list = []

    # Structural (5)
    feats.append(min(len(content) / 10_000, 10.0))
    feats.append(min(len(lines) / 500, 10.0))
    feats.append(float(content.count("{")))
    feats.append(float(content.count("resource")))
    feats.append(float(bool(re.search(r"apiVersion:", content))))

    # Credential signals (8)
    for kw in ["password", "secret", "api_key", "access_key", "private_key",
                "token", "credential", "auth"]:
        feats.append(float(lower.count(kw)))

    # Network signals (8)
    for kw in ["0.0.0.0", "::/0", "public", "ingress", "egress",
                "security_group", "firewall", "cidr"]:
        feats.append(float(lower.count(kw)))

    # Crypto signals (8)
    for kw in ["encrypt", "kms", "ssl", "tls", "https", "certificate",
                "aes", "sha"]:
        feats.append(float(lower.count(kw)))

    # IAM signals (6)
    for kw in ["iam", "role", "policy", "principal", "assume_role", "admin"]:
        feats.append(float(lower.count(kw)))

    # Logging/monitoring (5)
    for kw in ["logging", "monitoring", "cloudtrail", "audit", "log_group"]:
        feats.append(float(lower.count(kw)))

    feats = feats[:40]
    while len(feats) < 40:
        feats.append(0.0)
    return feats


@app.post("/rules-scan", response_model=RulesScanResponse)
async def rules_scan(request: RulesScanRequest):
    """
    Scan file using rules engine only.
    """
    try:
        try:
            from rules.rules_engine.engine import scan_single_file
            from pathlib import Path
            
            # Run rules scan
            findings = scan_single_file(
                file_path=Path(request.file_path),
                content=request.file_content
            )
        except ImportError:
            # Rules engine not available, return empty findings
            findings = []
        
        # Count by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for f in findings:
            severity = f.get('severity', 'low').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Calculate risk score based on severity weights
        # Critical: 1.0, High: 0.75, Medium: 0.5, Low: 0.25, Info: 0.1
        risk_score = 0.0
        if len(findings) > 0:
            severity_weights = {'critical': 1.0, 'high': 0.75, 'medium': 0.5, 'low': 0.25, 'info': 0.1}
            weighted_sum = sum(
                severity_counts.get(sev, 0) * weight 
                for sev, weight in severity_weights.items()
            )
            # Normalize to 0-1 range (assuming max 10 findings for normalization)
            risk_score = min(weighted_sum / 10.0, 1.0)
        
        # Convert to schema
        finding_objs = [Finding(**f) for f in findings]
        
        return RulesScanResponse(
            findings=finding_objs,
            total_findings=len(findings),
            critical_count=severity_counts['critical'],
            high_count=severity_counts['high'],
            medium_count=severity_counts['medium'],
            low_count=severity_counts['low'],
            risk_score=risk_score,
            severity_counts=severity_counts
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rules scan failed: {str(e)}")


@app.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest):
    """
    Get LLM explanations and remediations for findings.
    """
    try:
        try:
            from rules.rules_engine.llm_reasoner import get_llm_explanation_and_remediation
            
            explained_findings = []
            
            for finding in request.findings:
                # Get LLM explanation
                llm_result = get_llm_explanation_and_remediation(
                    file_content=request.file_content,
                    finding=finding,
                    provider=settings.llm_provider,
                    api_key=settings.openai_api_key if settings.llm_provider == 'openai' else settings.anthropic_api_key
                )
                
                # Create explained finding
                explained = ExplainedFinding(
                    **finding,
                    llm_explanation=llm_result.get('explanation'),
                    llm_remediation=llm_result.get('remediation')
                )
                explained_findings.append(explained)
        except ImportError:
            # LLM reasoner not available, return findings without explanation
            explained_findings = [ExplainedFinding(**finding) for finding in request.findings]
        
        return ExplainResponse(findings=explained_findings)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@app.post("/aggregate", response_model=AggregateResponse)
async def aggregate(request: AggregateRequest):
    """
    Get unified risk score aggregating ALL 6 scanners:
    - ML prediction
    - Rules-based scanning
    - LLM reasoning
    - Secrets detection (NEW)
    - CVE scanning (NEW)
    - Compliance validation (NEW)
    """
    try:
        # Import integrated scanner
        import sys
        from pathlib import Path
        
        # Add api directory to path
        api_dir = Path(__file__).parent.parent.parent / "api"
        if str(api_dir) not in sys.path:
            sys.path.insert(0, str(api_dir))
        
        from scanners.integrated_scanner import get_integrated_scanner
        
        # Get ML prediction
        ml_result = await predict(PredictRequest(
            file_path=request.file_path,
            file_content=request.file_content
        ))
        
        # Get rules findings
        rules_result = await rules_scan(RulesScanRequest(
            file_path=request.file_path,
            file_content=request.file_content
        ))
        
        # Run integrated scanning (Secrets + CVE + Compliance)
        scanner = get_integrated_scanner()
        integrated_result = scanner.scan_file_integrated(
            file_path=request.file_path,
            content=request.file_content,
            rules_findings=[],
            ml_score=ml_result.risk_score,
            llm_findings=[]
        )
        
        # Extract scores from integrated scanner
        ml_score = ml_result.risk_score
        rules_score = min(len(rules_result.findings) / 10.0, 1.0)  # Normalize by count
        llm_score = getattr(request, 'llm_insights', [{}])[0].get('confidence', 0.5) if hasattr(request, 'llm_insights') and request.llm_insights else 0.5
        secrets_risk = integrated_result['scores'].get('secrets_risk', 0) / 100.0  # Normalize
        cve_risk = integrated_result['scores'].get('cve_risk', 0) / 100.0  # Normalize
        compliance_risk = integrated_result['scores'].get('compliance_risk', 0) / 100.0  # Normalize
        
        # Enhanced unified risk: weighted average of ALL 6 scanners
        # Weight distribution: ML=20%, Rules=25%, LLM=15%, Secrets=25%, CVE=10%, Compliance=5%
        unified = (
            ml_score * 0.20 + 
            rules_score * 0.25 + 
            llm_score * 0.15 +
            secrets_risk * 0.25 +
            cve_risk * 0.10 +
            compliance_risk * 0.05
        )
        
        # Merge ALL findings from all scanners
        findings = []
        
        # Rules findings
        for f in rules_result.findings:
            findings.append(ExplainedFinding(
                **f.model_dump(),
                llm_explanation=None,
                llm_remediation=None
            ))
        
        # Secrets findings
        for f in integrated_result['findings']['secrets']:
            findings.append(ExplainedFinding(
                type=f.get('type', 'UNKNOWN'),
                severity=f.get('severity', 'MEDIUM'),
                category='secrets',
                title=f.get('title', 'Secret Detected'),
                description=f.get('description', ''),
                line_number=f.get('line_number', 0),
                code_snippet=f.get('code_snippet', ''),
                remediation='; '.join(f.get('remediation_steps', [])),
                llm_explanation=None,
                llm_remediation=None
            ))
        
        # CVE findings
        for f in integrated_result['findings']['cve']:
            findings.append(ExplainedFinding(
                type=f.get('type', 'CVE'),
                severity=f.get('severity', 'MEDIUM'),
                category='cve',
                title=f.get('title', 'CVE Detected'),
                description=f.get('description', ''),
                line_number=f.get('line_number', 0),
                code_snippet=f.get('code_snippet', ''),
                remediation='; '.join(f.get('remediation_steps', [])),
                llm_explanation=None,
                llm_remediation=None
            ))
        
        # Compliance findings
        for f in integrated_result['findings']['compliance']:
            findings.append(ExplainedFinding(
                type=f.get('type', 'COMPLIANCE'),
                severity=f.get('severity', 'MEDIUM'),
                category='compliance',
                title=f.get('title', 'Compliance Issue'),
                description=f.get('description', ''),
                line_number=0,
                code_snippet='',
                remediation='; '.join(f.get('remediation_steps', [])),
                llm_explanation=None,
                llm_remediation=None
            ))
        
        # Enhanced reasoning with scanner breakdown
        scanner_summary = integrated_result['summary']['by_scanner']
        reasoning = (
            f"Unified risk score: {unified:.2f}/1.0 computed from {len(findings)} findings across 6 scanners. "
            f"Scanner breakdown: ML={ml_score:.2f}, Rules={rules_score:.2f}, LLM={llm_score:.2f}, "
            f"Secrets={secrets_risk:.2f}, CVE={cve_risk:.2f}, Compliance={compliance_risk:.2f}. "
            f"Findings: {scanner_summary.get('secrets', 0)} secrets, "
            f"{scanner_summary.get('cve', 0)} CVEs, "
            f"{scanner_summary.get('compliance', 0)} compliance issues."
        )
        
        return AggregateResponse(
            unified_risk_score=unified,
            ml_score=ml_score,
            rules_score=rules_score,
            llm_score=llm_score,
            findings=findings,
            reasoning=reasoning
        )
        
    except Exception as e:
        import traceback
        logger.error("Aggregation error: %s\n%s", str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(e)}")


@app.post("/train/online", response_model=OnlineTrainResponse)
async def train_online(request: OnlineTrainRequest):
    """
    Perform online learning with new labeled data using SGDClassifier.
    """
    try:
        from ml_service.trainer import OnlineLearner
        
        # Initialize online learner
        learner = OnlineLearner(
            models_dir=settings.ml_models_path,
            features_dir=settings.features_path
        )
        
        # Prepare training data
        X_data = []
        y_labels = []
        
        for sample in request.training_data:
            # Extract features
            features = learner.extract_features(
                file_path=sample.file_path,
                content=sample.file_content
            )
            X_data.append(features)
            y_labels.append(sample.label)
        
        # Partial fit
        metrics = learner.partial_fit(X_data, y_labels)
        
        # Register training session and save versioned model
        learner.register_training(
            metrics=metrics,
            training_samples=len(request.training_data),
            metadata=request.metadata
        )
        
        return OnlineTrainResponse(
            status="completed",
            samples_processed=len(request.training_data),
            accuracy=metrics.get('accuracy'),
            precision=metrics.get('precision'),
            recall=metrics.get('recall'),
            f1_score=metrics.get('f1_score'),
            metadata={
                **metrics.get('metadata', {}),
                'version': learner.version,
                'registry_updated': True
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Online training failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
