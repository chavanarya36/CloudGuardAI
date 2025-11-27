import sys
import os
from pathlib import Path

# Add parent directory to path to import existing CloudGuard modules
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, HTTPException
from ml_service.config import settings
from ml_service.schemas import (
    PredictRequest, PredictResponse,
    RulesScanRequest, RulesScanResponse,
    ExplainRequest, ExplainResponse,
    AggregateRequest, AggregateResponse,
    OnlineTrainRequest, OnlineTrainResponse,
    Finding, ExplainedFinding
)

app = FastAPI(
    title="CloudGuard ML Service",
    description="ML service for security scanning with models, rules engine, and LLM reasoning",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "service": "CloudGuard ML Service",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Get ML prediction for a file using the ensemble model.
    """
    try:
        from cloudguard.predictor import CorePredictor
        
        # Initialize predictor (lazy load)
        predictor = CorePredictor(
            mode='hybrid',
            models_dir=settings.ml_models_path,
            features_dir=settings.features_path
        )
        
        # Get prediction
        result = predictor.predict_from_content(
            file_path=request.file_path,
            content=request.file_content
        )
        
        # Map score to category
        score = result.get('risk_score', 0.0)
        if score >= 0.8:
            prediction = 'critical'
        elif score >= 0.6:
            prediction = 'high'
        elif score >= 0.4:
            prediction = 'medium'
        else:
            prediction = 'low'
        
        return PredictResponse(
            risk_score=score,
            confidence=result.get('confidence', 0.0),
            prediction=prediction,
            features=result.get('features', {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/rules-scan", response_model=RulesScanResponse)
async def rules_scan(request: RulesScanRequest):
    """
    Scan file using rules engine only.
    """
    try:
        from rules_engine.engine import scan_single_file
        from pathlib import Path
        
        # Run rules scan
        findings = scan_single_file(
            file_path=Path(request.file_path),
            content=request.file_content
        )
        
        # Count by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for f in findings:
            severity = f.get('severity', 'low').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Convert to schema
        finding_objs = [Finding(**f) for f in findings]
        
        return RulesScanResponse(
            findings=finding_objs,
            total_findings=len(findings),
            critical_count=severity_counts['critical'],
            high_count=severity_counts['high'],
            medium_count=severity_counts['medium'],
            low_count=severity_counts['low']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rules scan failed: {str(e)}")


@app.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest):
    """
    Get LLM explanations and remediations for findings.
    """
    try:
        from llm_reasoner import get_llm_explanation_and_remediation
        
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
        
        return ExplainResponse(findings=explained_findings)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@app.post("/aggregate", response_model=AggregateResponse)
async def aggregate(request: AggregateRequest):
    """
    Get unified risk score aggregating ML, rules, and LLM scores.
    """
    try:
        from cloudguard.unified import compute_unified_risk
        
        # Compute unified risk (handles all internal calls)
        result = compute_unified_risk(
            file_path=request.file_path,
            file_content=request.file_content,
            models_dir=settings.ml_models_path,
            features_dir=settings.features_path,
            rules_dir=settings.rules_path,
            llm_provider=settings.llm_provider,
            llm_api_key=settings.openai_api_key if settings.llm_provider == 'openai' else settings.anthropic_api_key
        )
        
        # Convert findings to schema
        findings = [ExplainedFinding(**f) for f in result.get('findings', [])]
        
        return AggregateResponse(
            unified_risk_score=result.get('unified_risk_score', 0.0),
            ml_score=result.get('ml_score', 0.0),
            rules_score=result.get('rules_score', 0.0),
            llm_score=result.get('llm_score', 0.0),
            findings=findings,
            reasoning=result.get('reasoning')
        )
        
    except Exception as e:
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
        
        # Save updated model
        learner.save_model()
        
        return OnlineTrainResponse(
            status="completed",
            samples_processed=len(request.training_data),
            accuracy=metrics.get('accuracy'),
            precision=metrics.get('precision'),
            recall=metrics.get('recall'),
            f1_score=metrics.get('f1_score'),
            metadata=metrics.get('metadata', {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Online training failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
