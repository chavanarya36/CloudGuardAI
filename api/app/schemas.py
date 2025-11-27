from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SeverityEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


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
    severity: SeverityEnum
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    resource: Optional[str] = None
    llm_explanation: Optional[str] = None
    llm_remediation: Optional[str] = None
    certainty: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ScanResponse(BaseModel):
    id: int
    filename: str
    status: ScanStatusEnum
    unified_risk_score: Optional[float] = None
    ml_score: Optional[float] = None
    rules_score: Optional[float] = None
    llm_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    findings: List[FindingResponse] = []
    
    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    scan_id: int
    finding_id: Optional[int] = None
    is_correct: Optional[int] = Field(None, ge=0, le=1)
    adjusted_severity: Optional[SeverityEnum] = None
    user_comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    scan_id: int
    finding_id: Optional[int] = None
    is_correct: Optional[int] = None
    adjusted_severity: Optional[SeverityEnum] = None
    user_comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ModelStatusResponse(BaseModel):
    active_version: Optional[str] = None
    model_type: Optional[str] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    training_samples: Optional[int] = None
    created_at: Optional[datetime] = None
    total_scans: int = 0
    total_feedback: int = 0
    pending_retraining_samples: int = 0


class RetrainRequest(BaseModel):
    force: bool = False
    min_samples: int = 100


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str
