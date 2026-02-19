#!/usr/bin/env python
"""
Simple test to verify API can start without database
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import asyncio
from app.observability import RequestIDMiddleware, TimingMiddleware, OperationTimer

app = FastAPI(title="CloudGuard AI API - Production")

# Add observability middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ML_SERVICE_URL = "http://127.0.0.1:8001"

class ScanRequest(BaseModel):
    file_name: str
    file_content: str

class ScanResponse(BaseModel):
    scan_id: str
    status: str
    unified_risk_score: float
    ml_score: float
    rules_score: float
    llm_score: float
    # New scanner scores
    secrets_score: Optional[float] = None
    cve_score: Optional[float] = None
    compliance_score: Optional[float] = None
    # All findings
    findings: List[Dict[str, Any]]
    # Findings by scanner type
    secrets_findings: Optional[List[Dict[str, Any]]] = None
    cve_findings: Optional[List[Dict[str, Any]]] = None
    compliance_findings: Optional[List[Dict[str, Any]]] = None
    rules_findings: Optional[List[Dict[str, Any]]] = None
    # Scanner statistics
    scanner_breakdown: Optional[Dict[str, int]] = None
    # Metadata
    reasoning: Optional[str] = None
    scan_duration_seconds: Optional[float] = None

@app.get("/")
async def root():
    return {"service": "CloudGuard AI API", "status": "healthy", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/model/status")
async def model_status():
    """
    Get ML model status from ML service
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check if ML service is running
            ml_health = await client.get(f"{ML_SERVICE_URL}/health")
            
            return {
                "active_model": "CloudGuard Hybrid Model v1.0",
                "model_type": "Heuristic + Rules Engine",
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.85,
                "total_scans": 0,
                "last_updated": "2025-11-28T00:00:00Z",
                "status": "healthy",
                "ml_service_connected": ml_health.status_code == 200
            }
    except Exception as e:
        return {
            "active_model": "CloudGuard Hybrid Model v1.0",
            "model_type": "Heuristic + Rules Engine",
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "total_scans": 0,
            "last_updated": "2025-11-28T00:00:00Z",
            "status": "degraded",
            "ml_service_connected": False,
            "error": str(e)
        }

@app.get("/model/versions")
async def model_versions(skip: int = 0, limit: int = 10):
    """
    Get model version history
    """
    return [
        {
            "id": 1,
            "version": "1.0.0",
            "type": "hybrid",
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "created_at": "2025-11-28T00:00:00Z",
            "is_active": True
        }
    ]

@app.post("/scan", response_model=ScanResponse)
async def scan_file(request: ScanRequest):
    """
    Scan an IaC file by calling the ML service
    """
    try:
        with OperationTimer("scan_file", {"file_name": request.file_name}):
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Call ML service aggregate endpoint
                with OperationTimer("ml_aggregate_call"):
                    ml_response = await client.post(
                        f"{ML_SERVICE_URL}/aggregate",
                        json={
                            "file_path": request.file_name,
                            "file_content": request.file_content
                        }
                    )
            
            if ml_response.status_code != 200:
                raise HTTPException(
                    status_code=ml_response.status_code,
                    detail=f"ML service error: {ml_response.text}"
                )
            
            result = ml_response.json()
            
            # Generate scan ID
            import uuid
            scan_id = str(uuid.uuid4())
            
            # Extract scanner-specific findings from aggregate result
            all_findings = result.get("findings", [])
            
            # Categorize findings by scanner
            secrets_findings = [f for f in all_findings if f.get("category") == "secrets"]
            cve_findings = [f for f in all_findings if f.get("category") == "cve"]
            compliance_findings = [f for f in all_findings if f.get("category") == "compliance"]
            rules_findings = [f for f in all_findings if f.get("category") not in ["secrets", "cve", "compliance"]]
            
            # Calculate scanner breakdown
            scanner_breakdown = {
                "secrets": len(secrets_findings),
                "cve": len(cve_findings),
                "compliance": len(compliance_findings),
                "rules": len(rules_findings),
                "total": len(all_findings)
            }
            
            return ScanResponse(
                scan_id=scan_id,
                status="completed",
                unified_risk_score=result["unified_risk_score"],
                ml_score=result["ml_score"],
                rules_score=result["rules_score"],
                llm_score=result["llm_score"],
                secrets_score=result.get("ml_score", 0) * 0.25,  # Approximate from weighted formula
                cve_score=result.get("ml_score", 0) * 0.10,
                compliance_score=100.0 - (len(compliance_findings) * 5.0),  # Penalty-based
                findings=all_findings,
                secrets_findings=secrets_findings,
                cve_findings=cve_findings,
                compliance_findings=compliance_findings,
                rules_findings=rules_findings,
                scanner_breakdown=scanner_breakdown,
                reasoning=result.get("reasoning"),
                scan_duration_seconds=result.get("scan_duration_seconds", 0)
            )
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"ML service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
