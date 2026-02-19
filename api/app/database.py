"""Database configuration and service layer"""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.deduplicator import FindingDeduplicator

# Import models from the unified models.py (single source of truth)
try:
    from .models import Scan, Finding, Feedback, ModelVersion
except ImportError:
    try:
        from app.models import Scan, Finding, Feedback, ModelVersion
    except ImportError:
        # Fallback for when models aren't yet created
        Scan = Finding = Feedback = ModelVersion = None

try:
    from app.config import settings
    DATABASE_URL = settings.database_url
except (ImportError, AttributeError):
    # Fallback to environment variable or SQLite
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cloudguard.db")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


def get_db():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


class DatabaseService:
    """Service class for database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== Scan Operations ==========
    
    def create_scan(
        self,
        filename: str,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        request_id: Optional[str] = None
    ):
        """Create a new scan record"""
        if not Scan:
            raise RuntimeError("Database models not available")
        
        scan = Scan(
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            request_id=request_id,
            status="pending"
        )
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)
        return scan
    
    def update_scan_results(
        self,
        scan_id: int,
        unified_risk_score: float,
        supervised_probability: Optional[float] = None,
        unsupervised_probability: Optional[float] = None,
        ml_score: Optional[float] = None,
        rules_score: Optional[float] = None,
        llm_score: Optional[float] = None,
        secrets_score: Optional[float] = None,
        cve_score: Optional[float] = None,
        compliance_score: Optional[float] = None,
        scanner_breakdown: Optional[Dict[str, int]] = None,
        scan_duration_ms: Optional[int] = None,
        status: str = "completed"
    ):
        """Update scan with results including new scanner scores"""
        scan = self.db.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            scan.unified_risk_score = unified_risk_score
            scan.supervised_probability = supervised_probability
            scan.unsupervised_probability = unsupervised_probability
            scan.ml_score = ml_score
            scan.rules_score = rules_score
            scan.llm_score = llm_score
            scan.secrets_score = secrets_score
            scan.cve_score = cve_score
            scan.compliance_score = compliance_score
            scan.scanner_breakdown = scanner_breakdown
            scan.scan_duration_ms = scan_duration_ms
            scan.status = status
            self.db.commit()
            self.db.refresh(scan)
        return scan
    
    def get_scan(self, scan_id: int):
        """Get scan by ID"""
        return self.db.query(Scan).filter(Scan.id == scan_id).first()
    
    def list_scans(self, limit: int = 100, offset: int = 0):
        """List recent scans"""
        return self.db.query(Scan).order_by(desc(Scan.created_at)).offset(offset).limit(limit).all()
    
    # ========== Finding Operations ==========
    
    def create_finding(
        self,
        scan_id: int,
        severity: str,
        description: str,
        rule_id: Optional[str] = None,
        llm_certainty: Optional[float] = None,
        llm_explanation_short: Optional[str] = None,
        llm_remediation: Optional[str] = None,
        code_snippet: Optional[str] = None,
        line_number: Optional[int] = None,
        category: Optional[str] = None,
        scanner: Optional[str] = None,
        cve_id: Optional[str] = None,
        cvss_score: Optional[float] = None,
        compliance_framework: Optional[str] = None,
        control_id: Optional[str] = None,
        remediation_steps: Optional[List[str]] = None,
        references: Optional[List[str]] = None,
        file_path: Optional[str] = None,
        resource: Optional[str] = None,
        title: Optional[str] = None
    ):
        """Create a new finding with scanner-specific fields"""
        if not Finding:
            raise RuntimeError("Database models not available")
        
        finding = Finding(
            scan_id=scan_id,
            severity=severity,
            description=description,
            rule_id=rule_id,
            llm_certainty=llm_certainty,
            llm_explanation_short=llm_explanation_short,
            llm_remediation=llm_remediation,
            code_snippet=code_snippet,
            line_number=line_number,
            category=category,
            scanner=scanner,
            cve_id=cve_id,
            cvss_score=cvss_score,
            compliance_framework=compliance_framework,
            control_id=control_id,
            remediation_steps=remediation_steps,
            references=references,
            file_path=file_path,
            resource=resource,
            title=title
        )
        self.db.add(finding)
        self.db.commit()
        self.db.refresh(finding)
        return finding
    
    def create_finding_with_deduplication(
        self,
        scan_id: int,
        severity: str,
        description: str,
        rule_id: Optional[str] = None,
        category: Optional[str] = None,
        scanner: Optional[str] = None,
        cve_id: Optional[str] = None,
        control_id: Optional[str] = None,
        file_path: Optional[str] = None,
        resource: Optional[str] = None,
        **kwargs
    ):
        """
        Create a finding with deduplication support.
        If a matching finding exists, updates occurrence count instead of creating duplicate.
        """
        # Generate finding hash
        finding_hash = FindingDeduplicator.generate_finding_hash(
            scanner=scanner,
            severity=severity,
            description=description,
            file_path=file_path,
            resource=resource,
            cve_id=cve_id,
            rule_id=rule_id,
            control_id=control_id
        )
        
        # Check if this finding already exists (within last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        existing_finding = self.db.query(Finding).filter(
            Finding.finding_hash == finding_hash,
            Finding.created_at >= thirty_days_ago,
            Finding.is_suppressed == False
        ).order_by(desc(Finding.last_seen)).first()
        
        if existing_finding:
            # Update existing finding
            existing_finding.last_seen = datetime.utcnow()
            existing_finding.occurrence_count += 1
            
            # Update severity if new one is more severe
            severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'INFO': 0}
            if severity_order.get(severity.upper(), 0) > severity_order.get(existing_finding.severity.upper(), 0):
                existing_finding.severity = severity
            
            self.db.commit()
            self.db.refresh(existing_finding)
            return existing_finding
        else:
            # Create new finding
            finding = Finding(
                scan_id=scan_id,
                severity=severity,
                description=description,
                rule_id=rule_id,
                category=category,
                scanner=scanner,
                cve_id=cve_id,
                control_id=control_id,
                file_path=file_path,
                resource=resource,
                finding_hash=finding_hash,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                occurrence_count=1,
                **kwargs
            )
            self.db.add(finding)
            self.db.commit()
            self.db.refresh(finding)
            return finding
    
    def suppress_finding(self, finding_id: int):
        """Mark a finding as suppressed (will not appear in deduplication checks)"""
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if finding:
            finding.is_suppressed = True
            self.db.commit()
        return finding
    
    def get_duplicate_findings(self, finding_hash: str, limit: int = 10):
        """Get all occurrences of a finding by its hash"""
        return self.db.query(Finding).filter(
            Finding.finding_hash == finding_hash
        ).order_by(desc(Finding.last_seen)).limit(limit).all()
    
    # ========== Model Version Operations ==========
    
    def get_active_model_version(self, model_type: str = "ensemble"):
        """Get currently active model version"""
        if not ModelVersion:
            return None
        return self.db.query(ModelVersion).filter(
            ModelVersion.model_type == model_type,
            ModelVersion.is_active == True
        ).first()
    
    def list_model_versions(self, model_type: Optional[str] = None, limit: int = 10):
        """List model versions"""
        if not ModelVersion:
            return []
        query = self.db.query(ModelVersion).order_by(desc(ModelVersion.created_at))
        if model_type:
            query = query.filter(ModelVersion.model_type == model_type)
        return query.limit(limit).all()
    
    # ========== Analytics Operations ==========
    
    def get_total_scans(self) -> int:
        """Get total number of scans"""
        if not Scan:
            return 0
        return self.db.query(Scan).count()
    
    def get_total_feedback(self) -> int:
        """Get total number of feedback entries"""
        if not Feedback:
            return 0
        return self.db.query(Feedback).count()
