"""Seed the database with an active model"""
from app.database import SessionLocal
from app.models import ModelVersion
from datetime import datetime

db = SessionLocal()

# Check if model already exists
existing = db.query(ModelVersion).filter(ModelVersion.is_active == 1).first()
if existing:
    print(f"Active model already exists: {existing.version}")
else:
    # Create initial model record with baseline metrics.
    # Note: these are conservative estimates for an untrained seed model.
    # Real metrics are populated by the online trainer after feedback-driven
    # retraining cycles.
    model = ModelVersion(
        version='v1.0.0',
        model_type='ensemble',
        accuracy=0.70,
        precision=0.65,
        recall=0.75,
        f1_score=0.70,
        training_samples=0,
        is_active=1,
        created_at=datetime.utcnow()
    )
    db.add(model)
    db.commit()
    print(f"Created active model: {model.version}")

db.close()
