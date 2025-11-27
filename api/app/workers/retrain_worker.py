import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Feedback, ModelVersion
from app.config import settings


def retrain_model():
    """
    Worker function to retrain model with new feedback data.
    Uses online learning with SGDClassifier via ML service.
    """
    db = SessionLocal()
    try:
        # Get feedback with labels
        feedbacks = db.query(Feedback).filter(
            Feedback.is_correct.isnot(None)
        ).all()
        
        if not feedbacks:
            return {"status": "skipped", "reason": "No feedback data"}
        
        # Prepare training data
        training_data = []
        for fb in feedbacks:
            if fb.scan and fb.scan.file_content:
                training_data.append({
                    "file_path": fb.scan.filename,
                    "file_content": fb.scan.file_content,
                    "label": fb.is_correct,
                    "adjusted_severity": fb.adjusted_severity.value if fb.adjusted_severity else None
                })
        
        # Call ML service for online learning
        ml_url = f"{settings.ml_service_url}/train/online"
        
        with httpx.Client(timeout=1800.0) as client:  # 30 min timeout
            response = client.post(
                ml_url,
                json={"training_data": training_data}
            )
            response.raise_for_status()
            result = response.json()
        
        # Create new model version record
        version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_version = ModelVersion(
            version=version,
            model_type="online_learner",
            accuracy=result.get("accuracy"),
            precision=result.get("precision"),
            recall=result.get("recall"),
            f1_score=result.get("f1_score"),
            training_samples=len(training_data),
            metadata=result.get("metadata", {}),
            is_active=1
        )
        
        # Deactivate old models
        db.query(ModelVersion).update({"is_active": 0})
        
        db.add(model_version)
        db.commit()
        
        return {
            "status": "completed",
            "version": version,
            "samples": len(training_data),
            "metrics": {
                "accuracy": result.get("accuracy"),
                "precision": result.get("precision"),
                "recall": result.get("recall"),
                "f1_score": result.get("f1_score")
            }
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()
