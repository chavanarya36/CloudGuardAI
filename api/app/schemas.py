from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SeverityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    @classmethod
    def _missing_(cls, value):
        """Accept both uppercase and lowercase severity values"""
        if isinstance(value, str):
            upper_val = value.upper()
            for member in cls:
                if member.value == upper_val:
                    return member
        return None


class ScanStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanCreate(BaseModel):
    filename: str
    file_content: str


class FindingResponse(BaseModel):
    id: int
    rule_id: str
    severity: str  # Accept any case, normalize on output
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    resource: Optional[str] = None
    llm_explanation: Optional[str] = None
    llm_explanation_short: Optional[str] = None  # Added for enriched schema
    llm_remediation: Optional[str] = None
    certainty: Optional[float] = None
    llm_certainty: Optional[float] = None  # Added for enriched schema
    meta_data: Optional[Dict[str, Any]] = None
    # New scanner-specific fields
    category: Optional[str] = None  # secrets, cve, compliance, rules, ml, llm
    scanner: Optional[str] = None  # Which scanner detected this
    cve_id: Optional[str] = None  # For CVE findings
    cvss_score: Optional[float] = None  # For CVE findings
    compliance_framework: Optional[str] = None  # For compliance findings
    control_id: Optional[str] = None  # For compliance findings (e.g., CIS 1.4)
    remediation_steps: Optional[List[str]] = None  # Step-by-step remediation
    references: Optional[List[str]] = None  # External references
    # Deduplication fields (Phase 2, Step 2.4)
    finding_hash: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    occurrence_count: Optional[int] = None
    is_suppressed: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ScanResponse(BaseModel):
    id: int
    filename: str
    status: ScanStatusEnum
    unified_risk_score: Optional[float] = None
    supervised_probability: Optional[float] = None  # Added for enriched schema
    unsupervised_probability: Optional[float] = None  # Added for enriched schema
    ml_score: Optional[float] = None
    rules_score: Optional[float] = None
    llm_score: Optional[float] = None
    # New scanner scores
    secrets_score: Optional[float] = None
    cve_score: Optional[float] = None
    compliance_score: Optional[float] = None  # 0-100, higher is better
    risk_score: Optional[float] = None
    severity_counts: Optional[Dict[str, int]] = None
    total_findings: Optional[int] = None
    critical_count: Optional[int] = None
    high_count: Optional[int] = None
    medium_count: Optional[int] = None
    low_count: Optional[int] = None
    scan_duration_ms: Optional[int] = None  # Added for enriched schema
    request_id: Optional[str] = None  # Added for enriched schema
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    findings: List[FindingResponse] = []
    # Scanner breakdown
    scanner_breakdown: Optional[Dict[str, int]] = None  # Findings count per scanner category

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    scan_id: int
    finding_id: Optional[int] = None
    is_correct: Optional[int] = Field(None, ge=0, le=1)
    adjusted_severity: Optional[SeverityEnum] = None
    user_comment: Optional[str] = None
    # Enriched schema additions
    accepted_prediction: Optional[bool] = None
    actual_risk_level: Optional[str] = None
    feedback_type: Optional[str] = None  # "accurate", "false_positive", "false_negative"
    model_version: Optional[str] = None
    # Scanner-specific feedback (Phase 2, Step 2.5)
    scanner_type: Optional[str] = None  # ML, Rules, LLM, Secrets, CVE, Compliance


class FeedbackResponse(BaseModel):
    id: int
    scan_id: int
    finding_id: Optional[int] = None
    is_correct: Optional[int] = None
    adjusted_severity: Optional[SeverityEnum] = None
    user_comment: Optional[str] = None
    scanner_type: Optional[str] = None  # Scanner-specific feedback
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelVersionDetail(BaseModel):
    """Individual model version detail"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    version: str
    model_type: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    training_samples: Optional[int] = None
    drift_score: Optional[float] = None
    is_active: bool
    created_at: datetime


class ModelStatusResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    active_version: Optional[str] = None
    model_type: Optional[str] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    training_samples: Optional[int] = None
    drift_score: Optional[float] = None  # Added for enriched schema
    created_at: Optional[datetime] = None
    total_scans: int = 0
    total_feedback: int = 0
    pending_retraining_samples: int = 0
    drift_detected: bool = False  # Added for enriched schema
    all_versions: List[ModelVersionDetail] = []  # Added for enriched schema


class RetrainRequest(BaseModel):
    force: bool = False
    min_samples: int = 100


class TrainingResponse(BaseModel):
    """Training completion response"""
    new_version: str
    old_version: Optional[str] = None
    samples_used: int
    accuracy_improvement: Optional[float] = None
    training_duration_ms: int
    message: str


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str
