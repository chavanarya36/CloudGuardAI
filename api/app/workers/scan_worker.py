import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Scan, Finding, ScanStatus
from app.config import settings


def process_scan(scan_id: int):
    """
    Worker function to process a scan asynchronously.
    Calls ML service and stores results.
    """
    db = SessionLocal()
    try:
        # Get scan
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return {"error": "Scan not found"}
        
        # Update status
        scan.status = ScanStatus.PROCESSING
        db.commit()
        
        # Call ML service for unified risk analysis
        ml_url = f"{settings.ml_service_url}/aggregate"
        
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                ml_url,
                json={
                    "file_path": scan.filename,
                    "file_content": scan.file_content
                }
            )
            response.raise_for_status()
            result = response.json()
        
        # Update scan with results
        scan.unified_risk_score = result.get("unified_risk_score")
        scan.ml_score = result.get("ml_score")
        scan.rules_score = result.get("rules_score")
        scan.llm_score = result.get("llm_score")
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow()
        
        # Store findings
        for finding_data in result.get("findings", []):
            finding = Finding(
                scan_id=scan.id,
                rule_id=finding_data.get("rule_id", "unknown"),
                severity=finding_data.get("severity", "low"),
                title=finding_data.get("title", "Untitled"),
                description=finding_data.get("description"),
                file_path=finding_data.get("file_path"),
                line_number=finding_data.get("line_number"),
                code_snippet=finding_data.get("code_snippet"),
                resource=finding_data.get("resource"),
                llm_explanation=finding_data.get("llm_explanation"),
                llm_remediation=finding_data.get("llm_remediation"),
                certainty=finding_data.get("certainty"),
                metadata=finding_data.get("metadata", {})
            )
            db.add(finding)
        
        db.commit()
        
        return {"status": "completed", "scan_id": scan_id}
        
    except Exception as e:
        # Update scan with error
        if scan:
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            scan.completed_at = datetime.utcnow()
            db.commit()
        
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()
