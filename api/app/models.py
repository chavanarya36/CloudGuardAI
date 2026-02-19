from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum
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
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Scan(Base):
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String)
    file_content = Column(Text, nullable=False)
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING)
    unified_risk_score = Column(Float, default=0.0)
    supervised_probability = Column(Float, default=0.0)
    unsupervised_probability = Column(Float, default=0.0)
    ml_score = Column(Float, default=0.0)
    rules_score = Column(Float, default=0.0)
    llm_score = Column(Float, default=0.0)
    # New scanner scores (Phase 1)
    secrets_score = Column(Float)
    cve_score = Column(Float)
    compliance_score = Column(Float)  # 0-100, higher is better
    # Scanner breakdown
    scanner_breakdown = Column(JSON)
    risk_score = Column(Float, default=0.0)
    severity_counts = Column(JSON)
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    # Performance tracking
    scan_duration_ms = Column(Integer)
    request_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    rule_id = Column(String, nullable=False)
    severity = Column(String(20), nullable=False)  # Store as string for flexibility
    title = Column(String, nullable=False)
    description = Column(Text)
    # Scanner categorization
    category = Column(String(50), index=True)  # secrets, cve, compliance, rules, ml, llm
    scanner = Column(String(50))  # Which scanner detected this
    # CVE-specific fields
    cve_id = Column(String(50), index=True)
    cvss_score = Column(Float)
    # Compliance-specific fields
    compliance_framework = Column(String(100))
    control_id = Column(String(50))
    # Remediation and references
    remediation_steps = Column(JSON)
    references = Column(JSON)
    file_path = Column(String)
    line_number = Column(Integer)
    code_snippet = Column(Text)
    resource = Column(String)
    llm_explanation = Column(Text)
    llm_explanation_short = Column(Text)
    llm_remediation = Column(Text)
    certainty = Column(Float)
    llm_certainty = Column(Float)
    meta_data = Column(JSON)
    # Deduplication fields
    finding_hash = Column(String(64), index=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)
    is_suppressed = Column(Boolean, default=False)
    
    scan = relationship("Scan", back_populates="findings")
    feedbacks = relationship("Feedback", back_populates="finding", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    finding_id = Column(Integer, ForeignKey("findings.id"))
    is_correct = Column(Integer)  # 1 = correct, 0 = incorrect
    adjusted_severity = Column(String(20))
    user_comment = Column(Text)
    # Enriched feedback fields
    rating = Column(Integer)  # 1-5 stars
    accepted_prediction = Column(Boolean)
    actual_risk_level = Column(String(20))
    feedback_type = Column(String(50))  # accurate, false_positive, false_negative
    scanner_type = Column(String(50))  # Which scanner this feedback is for
    model_version = Column(String(20))
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
    drift_score = Column(Float)
    file_path = Column(String(255))
    meta_data = Column(JSON)
    is_active = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
