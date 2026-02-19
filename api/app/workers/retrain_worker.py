import httpx
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Feedback, ModelVersion
from app.config import settings
from app.adaptive_learning import learning_engine, FeedbackLabelTransformer

logger = logging.getLogger(__name__)


def retrain_model():
    """
    Worker function to retrain model with new feedback data.
    Uses online learning with SGDClassifier via ML service.

    Labels are derived correctly using FeedbackLabelTransformer:
      - is_correct=1 on a risky scan → label=1 (risky)
      - is_correct=0 on a risky scan → label=0 (false positive, actually safe)
      - feedback_type overrides when present
    """
    db = SessionLocal()
    try:
        # Get feedback with labels
        feedbacks = db.query(Feedback).filter(
            Feedback.is_correct.isnot(None)
        ).all()
        
        if not feedbacks:
            return {"status": "skipped", "reason": "No feedback data"}
        
        # Prepare training data with CORRECT label derivation
        transformer = FeedbackLabelTransformer()
        training_data = []
        for fb in feedbacks:
            if fb.scan and fb.scan.file_content:
                label = transformer.to_risk_label(
                    is_correct=fb.is_correct,
                    feedback_type=getattr(fb, "feedback_type", None),
                    scan_risk_score=fb.scan.risk_score or 0.5,
                )
                training_data.append({
                    "file_path": fb.scan.filename,
                    "file_content": fb.scan.file_content,
                    "label": label,
                    "adjusted_severity": fb.adjusted_severity.value if fb.adjusted_severity else None
                })
        
        if not training_data:
            return {"status": "skipped", "reason": "No usable training data"}

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

        # Notify adaptive learning engine
        metrics = {
            "accuracy": result.get("accuracy"),
            "precision": result.get("precision"),
            "recall": result.get("recall"),
            "f1_score": result.get("f1_score"),
            "samples": len(training_data),
            "version": version,
        }
        try:
            learning_engine.on_retrain_completed(metrics)
        except Exception:
            pass  # non-fatal

        logger.info(
            "✅ Retrain complete: v%s — %d samples, acc=%.3f, f1=%.3f",
            version, len(training_data),
            result.get("accuracy", 0), result.get("f1_score", 0),
        )
        
        return {
            "status": "completed",
            "version": version,
            "samples": len(training_data),
            "metrics": metrics,
        }
        
    except Exception as e:
        logger.error("Retrain failed: %s", e)
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()
