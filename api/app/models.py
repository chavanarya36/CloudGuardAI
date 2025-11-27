from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Scan(Base):
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String)
    file_content = Column(Text, nullable=False)
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING)
    unified_risk_score = Column(Float)
    ml_score = Column(Float)
    rules_score = Column(Float)
    llm_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    rule_id = Column(String, nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    file_path = Column(String)
    line_number = Column(Integer)
    code_snippet = Column(Text)
    resource = Column(String)
    llm_explanation = Column(Text)
    llm_remediation = Column(Text)
    certainty = Column(Float)
    metadata = Column(JSON)
    
    scan = relationship("Scan", back_populates="findings")
    feedbacks = relationship("Feedback", back_populates="finding", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    finding_id = Column(Integer, ForeignKey("findings.id"))
    is_correct = Column(Integer)  # 1 = correct, 0 = incorrect, None = not evaluated
    adjusted_severity = Column(Enum(Severity))
    user_comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    scan = relationship("Scan", back_populates="feedbacks")
    finding = relationship("Finding", back_populates="feedbacks")


class ModelVersion(Base):
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, unique=True, nullable=False)
    model_type = Column(String, nullable=False)  # 'ensemble', 'online_learner', etc.
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    training_samples = Column(Integer)
    metadata = Column(JSON)
    is_active = Column(Integer, default=0)  # 1 = active, 0 = inactive
    created_at = Column(DateTime, default=datetime.utcnow)
