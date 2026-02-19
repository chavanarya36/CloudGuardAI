from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class PredictRequest(BaseModel):
    file_path: str
    file_content: str


class PredictResponse(BaseModel):
    risk_score: float
    confidence: float
    prediction: str  # 'low', 'medium', 'high', 'critical'
    features: Optional[Dict[str, Any]] = None


class RulesScanRequest(BaseModel):
    file_path: str
    file_content: str


class Finding(BaseModel):
    rule_id: str
    severity: str
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    resource: Optional[str] = None
    certainty: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class RulesScanResponse(BaseModel):
    findings: List[Finding]
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    risk_score: float = 0.0
    severity_counts: Dict[str, int] = {}


class ExplainRequest(BaseModel):
    file_path: str
    file_content: str
    findings: List[Dict[str, Any]]


class ExplainedFinding(Finding):
    llm_explanation: Optional[str] = None
    llm_remediation: Optional[str] = None


class ExplainResponse(BaseModel):
    findings: List[ExplainedFinding]


class AggregateRequest(BaseModel):
    file_path: str
    file_content: str


class AggregateResponse(BaseModel):
    unified_risk_score: float
    ml_score: float
    rules_score: float
    llm_score: float
    findings: List[ExplainedFinding]
    reasoning: Optional[str] = None


class TrainingData(BaseModel):
    file_path: str
    file_content: str
    label: int  # 0 or 1
    adjusted_severity: Optional[str] = None


class OnlineTrainRequest(BaseModel):
    training_data: List[TrainingData]
    metadata: Optional[Dict[str, Any]] = None


class OnlineTrainResponse(BaseModel):
    status: str
    samples_processed: int
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
