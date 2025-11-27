from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import httpx
from app.config import settings
from app.database import get_db, engine, Base
from app.models import Scan, Finding, Feedback, ModelVersion, ScanStatus
from app.schemas import (
    ScanResponse, FeedbackCreate, FeedbackResponse,
    ModelStatusResponse, RetrainRequest, JobResponse, FindingResponse
)
from app.workers import enqueue_scan_job, enqueue_retrain_job

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CloudGuard AI API",
    description="REST API for security scanning with ML-powered risk assessment",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "CloudGuard AI API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/scan", response_model=JobResponse)
async def create_scan(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a file for security scanning.
    Returns a job ID for async processing.
    """
    # Read file content
    content = await file.read()
    file_content = content.decode('utf-8')
    
    # Create scan record
    scan = Scan(
        filename=file.filename,
        file_content=file_content,
        status=ScanStatus.PENDING
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # Enqueue async job
    job = enqueue_scan_job(scan.id)
    
    return JobResponse(
        job_id=job.id,
        status="queued",
        message=f"Scan {scan.id} queued for processing"
    )


@app.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: int, db: Session = Depends(get_db)):
    """Get scan results by ID."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.get("/scans", response_model=List[ScanResponse])
async def list_scans(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all scans."""
    scans = db.query(Scan).order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()
    return scans


@app.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submit feedback for a scan or finding.
    Used for online learning and model improvement.
    """
    # Validate scan exists
    scan = db.query(Scan).filter(Scan.id == feedback.scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Validate finding if provided
    if feedback.finding_id:
        finding = db.query(Finding).filter(Finding.id == feedback.finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
    
    # Create feedback
    db_feedback = Feedback(**feedback.dict())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback


@app.get("/feedback", response_model=List[FeedbackResponse])
async def list_feedback(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all feedback."""
    feedbacks = db.query(Feedback).order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
    return feedbacks


@app.get("/model/status", response_model=ModelStatusResponse)
async def get_model_status(db: Session = Depends(get_db)):
    """Get current model status and metrics."""
    # Get active model
    active_model = db.query(ModelVersion).filter(ModelVersion.is_active == 1).first()
    
    # Get statistics
    total_scans = db.query(Scan).count()
    total_feedback = db.query(Feedback).count()
    pending_feedback = db.query(Feedback).filter(Feedback.is_correct.isnot(None)).count()
    
    if active_model:
        return ModelStatusResponse(
            active_version=active_model.version,
            model_type=active_model.model_type,
            accuracy=active_model.accuracy,
            precision=active_model.precision,
            recall=active_model.recall,
            f1_score=active_model.f1_score,
            training_samples=active_model.training_samples,
            created_at=active_model.created_at,
            total_scans=total_scans,
            total_feedback=total_feedback,
            pending_retraining_samples=pending_feedback
        )
    
    return ModelStatusResponse(
        total_scans=total_scans,
        total_feedback=total_feedback,
        pending_retraining_samples=pending_feedback
    )


@app.post("/model/retrain", response_model=JobResponse)
async def retrain_model(
    request: RetrainRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger model retraining with new feedback data.
    Uses online learning with SGDClassifier.
    """
    # Check if enough feedback
    feedback_count = db.query(Feedback).filter(Feedback.is_correct.isnot(None)).count()
    
    if not request.force and feedback_count < request.min_samples:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough feedback for retraining. "
                   f"Need {request.min_samples}, have {feedback_count}. "
                   f"Use force=true to override."
        )
    
    # Enqueue retrain job
    job = enqueue_retrain_job()
    
    return JobResponse(
        job_id=job.id,
        status="queued",
        message=f"Retraining job queued with {feedback_count} samples"
    )


@app.get("/model/versions", response_model=List[ModelStatusResponse])
async def list_model_versions(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List all model versions."""
    versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        ModelStatusResponse(
            active_version=v.version,
            model_type=v.model_type,
            accuracy=v.accuracy,
            precision=v.precision,
            recall=v.recall,
            f1_score=v.f1_score,
            training_samples=v.training_samples,
            created_at=v.created_at
        )
        for v in versions
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
