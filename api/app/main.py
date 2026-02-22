from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case as sa_case
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import logging
import httpx
from app.config import settings
from app.database import get_db, engine, Base
from app.models import Scan, Finding, Feedback, ModelVersion, ScanStatus
from app.schemas import (
    ScanResponse, FeedbackCreate, FeedbackResponse,
    ModelStatusResponse, RetrainRequest, JobResponse, FindingResponse
)
from app.workers import enqueue_retrain_job
from app.adaptive_learning import learning_engine
from app.auth import get_current_user, optional_auth, AuthUser, create_jwt, generate_api_key
from app.rate_limiter import RateLimitMiddleware
from app.metrics import MetricsMiddleware, metrics
from scanners.integrated_scanner import get_integrated_scanner
from scanners.attack_path_analyzer import analyze_attack_paths

logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CloudGuard AI API",
    description="REST API for security scanning with ML-powered risk assessment",
    version="2.0.0"
)

# Middleware stack (order matters — outermost first)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "CloudGuard AI API",
        "version": app.version,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Metrics endpoint (Prometheus-compatible)
# ---------------------------------------------------------------------------

@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    # Update gauges from learning engine
    try:
        status = learning_engine.get_learning_status()
        metrics.learning_buffer_size = status.get("training_buffer_size", 0)
        metrics.drift_psi = status.get("drift", {}).get("psi_score", 0.0)
        metrics.discovered_patterns = status.get("patterns", {}).get("total_patterns", 0)
    except Exception:
        pass
    return metrics.render_prometheus()


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post("/auth/token")
async def create_token(subject: str = Form("api_client"), expires_minutes: int = Form(60)):
    """Generate a JWT access token (for development / service-to-service)."""
    token = create_jwt(subject, expires_minutes=expires_minutes)
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_minutes * 60}


@app.post("/auth/api-key")
async def create_api_key(user: AuthUser = Depends(get_current_user)):
    """Generate a new API key (requires existing authentication)."""
    key = generate_api_key()
    return {"api_key": key, "message": "Store this key securely — it cannot be retrieved again."}


@app.post("/scan", response_model=ScanResponse)
async def create_scan(
    file: UploadFile = File(...),
    scan_mode: str = Form("all"),
    db: Session = Depends(get_db)
):
    """
    Upload a file for security scanning.
    Process synchronously and return results.
    Scan modes: 'all' (complete AI), 'gnn' (GNN only), 'checkov' (compliance only)
    """
    # Read file content
    content = await file.read()
    file_content = content.decode('utf-8')
    
    # Create scan record
    scan = Scan(
        filename=file.filename,
        file_content=file_content,
        status=ScanStatus.PROCESSING
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # Process scan synchronously
    try:
        # Determine endpoint based on scan mode
        logger.debug("Received scan_mode = '%s'", scan_mode)
        if scan_mode == "gnn":
            endpoint = "/gnn-scan"
            scan_type = "GNN Attack Path Detection"
            logger.debug("Using GNN mode")
        elif scan_mode == "checkov":
            endpoint = "/checkov-scan"
            scan_type = "Checkov Compliance"
            logger.debug("Using Checkov mode")
        else:  # 'all' or default
            endpoint = "/rules-scan"
            scan_type = "Complete AI Scan"
            logger.debug("Using default mode (scan_mode='%s')", scan_mode)
        
        # Call ML service with retry + exponential backoff
        response = None
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{settings.ml_service_url}{endpoint}",
                        json={"file_path": file.filename, "file_content": file_content, "scan_mode": scan_mode},
                        timeout=30.0
                    )
                break  # success
            except httpx.TimeoutException:
                logger.warning("ML service timeout (attempt %d/%d) for %s", attempt, max_retries, scan_type)
                if attempt < max_retries:
                    await asyncio.sleep(1.0 * attempt)  # exponential backoff
            except Exception as ml_error:
                logger.warning("ML service error (attempt %d/%d) for %s: %s", attempt, max_retries, scan_type, ml_error)
                break  # non-timeout errors fail fast

        if response is None:
            logger.info("Using integrated scanner for local scanning...")
            
        if response and response.status_code == 200:
            result = response.json()
        else:
            # Use integrated scanner directly when ML service unavailable
            try:
                scanner = get_integrated_scanner()
                result = await asyncio.to_thread(scanner.scan_content, file_content, file.filename)
                logger.info("Local scan result: %d findings", result.get('total_findings', 0))
            except Exception as scan_error:
                logger.error("Integrated scanner error: %s", scan_error)
                result = {
                    "findings": [],
                    "total_findings": 0,
                    "risk_score": 0.0,
                    "severity_counts": {},
                    "scanners_used": []
                }

        # ── Always run CVE, Compliance & Secrets scanners locally ──
        # The ML service /rules-scan only returns rules findings, so we
        # run the remaining fast local scanners every time to ensure
        # full 6-scanner coverage.
        scanners_used = list(result.get("scanners_used", []))
        all_findings = list(result.get("findings", []))
        _gnn_graph_data = {}
        _gnn_attack_paths = []
        _gnn_summary = {}

        try:
            integrated = get_integrated_scanner()

            # Secrets scanner
            try:
                secrets_findings = await asyncio.to_thread(
                    integrated.scan_with_secrets_scanner, file_content, file.filename
                )
                if secrets_findings:
                    all_findings.extend(secrets_findings)
                    if "secrets" not in scanners_used:
                        scanners_used.append("secrets")
                    logger.info("Secrets scanner: %d findings", len(secrets_findings))
            except Exception as e:
                logger.warning("Secrets scanner error (non-fatal): %s", e)

            # CVE scanner
            try:
                cve_findings = await asyncio.to_thread(
                    integrated.scan_with_cve_scanner, file_content, file.filename
                )
                if cve_findings:
                    all_findings.extend(cve_findings)
                    if "cve" not in scanners_used:
                        scanners_used.append("cve")
                    logger.info("CVE scanner: %d findings", len(cve_findings))
            except Exception as e:
                logger.warning("CVE scanner error (non-fatal): %s", e)

            # Compliance scanner
            try:
                compliance_findings = await asyncio.to_thread(
                    integrated.scan_with_compliance_scanner, file_content, file.filename
                )
                if compliance_findings:
                    all_findings.extend(compliance_findings)
                    if "compliance" not in scanners_used:
                        scanners_used.append("compliance")
                    logger.info("Compliance scanner: %d findings", len(compliance_findings))
            except Exception as e:
                logger.warning("Compliance scanner error (non-fatal): %s", e)

            # ML scanner (prediction)
            try:
                ml_findings = await asyncio.to_thread(
                    integrated.scan_with_ml_scanner, file_content, file.filename
                )
                if ml_findings:
                    all_findings.extend(ml_findings)
                    if "ml" not in scanners_used:
                        scanners_used.append("ml")
                    logger.info("ML scanner: %d findings", len(ml_findings))
            except Exception as e:
                logger.warning("ML scanner error (non-fatal): %s", e)

            # GNN Attack Path Analyzer (graph-based attack chain detection)
            try:
                gnn_result = await asyncio.to_thread(
                    analyze_attack_paths, file_content, file.filename
                )
                gnn_findings = gnn_result.get("findings", [])
                if gnn_findings:
                    all_findings.extend(gnn_findings)
                    if "gnn" not in scanners_used:
                        scanners_used.append("gnn")
                    logger.info(
                        "GNN Attack Path Analyzer: %d findings, %d paths detected",
                        len(gnn_findings), gnn_result.get("summary", {}).get("total_paths", 0),
                    )
                # Store graph data and attack paths for the response
                _gnn_graph_data = gnn_result.get("graph", {})
                _gnn_attack_paths = gnn_result.get("attack_paths", [])
                _gnn_summary = gnn_result.get("summary", {})
            except Exception as e:
                logger.warning("GNN Attack Path Analyzer error (non-fatal): %s", e)
                _gnn_graph_data = {}
                _gnn_attack_paths = []
                _gnn_summary = {}

        except Exception as e:
            logger.warning("Additional scanners init error (non-fatal): %s", e)

        # ── Explainability enrichment ──────────────────────────────
        # Build rich descriptions with impact analysis and remediation
        # for every finding so users understand WHY an issue matters.
        _SCANNER_DISPLAY = {
            "rules": "Rules", "secrets": "Secrets", "cve": "CVE",
            "compliance": "Compliance", "ml": "ML", "llm": "LLM",
            "gnn": "GNN",
        }
        _IMPACT_DB = {
            "CRITICAL": "This could allow full system compromise, data breach, or unauthorized access to production infrastructure.",
            "HIGH": "This could lead to significant data exposure, privilege escalation, or service disruption.",
            "MEDIUM": "This could enable partial information disclosure or weaken the security posture.",
            "LOW": "This is a minor issue that could contribute to a larger attack chain.",
        }
        _CATEGORY_REMEDIATION = {
            "rules": [
                "Review the flagged configuration block",
                "Apply least-privilege and defense-in-depth principles",
                "Validate changes with terraform plan before applying",
                "Add automated policy checks in your CI/CD pipeline",
            ],
            "secrets": [
                "Remove the hardcoded secret from source code immediately",
                "Rotate the exposed credential (key, token, password)",
                "Use a secrets manager (AWS Secrets Manager, HashiCorp Vault)",
                "Add pre-commit hooks to prevent future secret commits",
            ],
            "cve": [
                "Upgrade the affected dependency to the fixed version",
                "Run dependency audit (npm audit fix / pip-audit / snyk)",
                "Review release notes for breaking changes before upgrading",
                "Pin dependency versions and enable automated update PRs",
            ],
            "compliance": [
                "Review the CIS Benchmark control referenced in this finding",
                "Update the Terraform resource to meet the compliance requirement",
                "Enable encryption, logging, or access controls as specified",
                "Validate compliance with terraform plan and manual review",
            ],
            "ml": [
                "Review the file for security misconfigurations flagged by ML model",
                "Cross-reference with rules and compliance findings",
                "Apply remediation steps from the most critical related findings",
            ],
        }

        for fd in all_findings:
            raw_scanner = (fd.get("scanner") or fd.get("category") or "rules").lower()
            display_scanner = _SCANNER_DISPLAY.get(raw_scanner, raw_scanner.capitalize())
            fd["scanner"] = display_scanner
            fd["category"] = fd.get("category") or raw_scanner

            # Build an enriched description with impact
            severity = (fd.get("severity") or "MEDIUM").upper()
            original_desc = fd.get("description") or fd.get("title") or ""
            impact = _IMPACT_DB.get(severity, "")
            if impact and impact not in original_desc:
                fd["description"] = f"{original_desc}\n\n**Impact:** {impact}"

            # Ensure remediation_steps exist
            if not fd.get("remediation_steps"):
                cat_key = raw_scanner if raw_scanner in _CATEGORY_REMEDIATION else "rules"
                fd["remediation_steps"] = _CATEGORY_REMEDIATION.get(cat_key, [])

        # ── Severity recount across ALL findings ──────────────────
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for fd in all_findings:
            sev = (fd.get("severity") or "MEDIUM").upper()
            severity_counts[sev.lower()] = severity_counts.get(sev.lower(), 0) + 1

        # ── Scanner-specific scores ───────────────────────────────
        _SCORE_WEIGHTS = {"CRITICAL": 1.0, "HIGH": 0.75, "MEDIUM": 0.5, "LOW": 0.25, "INFO": 0.1}
        scanner_scores = {}  # e.g. {"Secrets": 0.8, "CVE": 0.0, ...}
        for fd in all_findings:
            s = fd.get("scanner", "Rules")
            w = _SCORE_WEIGHTS.get((fd.get("severity") or "MEDIUM").upper(), 0.25)
            scanner_scores[s] = scanner_scores.get(s, 0.0) + w

        # Normalize each scanner score to 0-1
        for s in scanner_scores:
            scanner_scores[s] = min(scanner_scores[s] / 10.0, 1.0)

        # Overall risk_score
        risk_score = result.get("risk_score", 0.0)
        if all_findings and risk_score == 0:
            total_w = sum(_SCORE_WEIGHTS.get((f.get("severity") or "MEDIUM").upper(), 0.25) for f in all_findings)
            risk_score = min(total_w / 10.0, 1.0)

        # ── Update scan record ────────────────────────────────────
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow()
        scan.risk_score = risk_score
        scan.unified_risk_score = risk_score
        scan.supervised_probability = min(risk_score * 1.1, 1.0)
        scan.unsupervised_probability = max(risk_score * 0.9, 0.0)
        scan.ml_score = scanner_scores.get("ML", min(risk_score * 1.05, 1.0))
        scan.rules_score = scanner_scores.get("Rules", risk_score)
        scan.llm_score = scanner_scores.get("LLM", max(risk_score * 0.85, 0.0))
        scan.secrets_score = scanner_scores.get("Secrets", 0.0)
        scan.cve_score = scanner_scores.get("CVE", 0.0)
        scan.compliance_score = scanner_scores.get("Compliance", 0.0)
        scan.severity_counts = severity_counts
        scan.total_findings = len(all_findings)
        scan.critical_count = severity_counts.get("critical", 0)
        scan.high_count = severity_counts.get("high", 0)
        scan.medium_count = severity_counts.get("medium", 0)
        scan.low_count = severity_counts.get("low", 0)
        # scanner_breakdown stores finding *counts* per category (lowercase keys)
        # because the frontend filter buttons use e.g. scannerBreakdown.secrets
        scanner_counts = {}
        for fd in all_findings:
            cat = (fd.get("category") or "rules").lower()
            scanner_counts[cat] = scanner_counts.get(cat, 0) + 1
        scanner_counts["total"] = len(all_findings)
        scan.scanner_breakdown = scanner_counts

        # Store GNN attack path graph data for visualization
        try:
            scan.gnn_graph_data = {
                "graph": _gnn_graph_data,
                "attack_paths": [
                    {
                        "path_id": p.get("path_id"),
                        "entry_point": p.get("entry_point"),
                        "target": p.get("target"),
                        "hops": p.get("hops"),
                        "severity": p.get("severity"),
                        "severity_score": p.get("severity_score"),
                        "path_string": p.get("path_string"),
                        "narrative": p.get("narrative"),
                        "remediation": p.get("remediation"),
                        "chain": p.get("chain"),
                    }
                    for p in _gnn_attack_paths
                ],
                "summary": _gnn_summary,
            }
        except Exception:
            scan.gnn_graph_data = None

        # ── Save findings with full explainability ────────────────
        for finding_data in all_findings:
            finding = Finding(
                scan_id=scan.id,
                rule_id=finding_data.get("rule_id", finding_data.get("check_id", finding_data.get("type", "UNKNOWN"))),
                severity=finding_data.get("severity", "INFO"),
                title=finding_data.get("title", finding_data.get("description", "")[:100]),
                description=finding_data.get("description", ""),
                file_path=file.filename,
                line_number=finding_data.get("line_number", finding_data.get("line")),
                code_snippet=finding_data.get("code_snippet", finding_data.get("evidence", "")),
                resource=finding_data.get("resource", ""),
                certainty=finding_data.get("certainty", finding_data.get("confidence", 0.0)),
                # Scanner categorization
                scanner=finding_data.get("scanner", "Rules"),
                category=finding_data.get("category", "rules"),
                # CVE-specific fields
                cve_id=finding_data.get("cve_id"),
                cvss_score=finding_data.get("cvss_score"),
                # Compliance-specific fields
                compliance_framework=finding_data.get("compliance_framework"),
                control_id=finding_data.get("control_id"),
                # Remediation & references (explainability)
                remediation_steps=finding_data.get("remediation_steps"),
                references=finding_data.get("references"),
                # LLM explanations
                llm_explanation=finding_data.get("llm_explanation"),
                llm_remediation=finding_data.get("llm_remediation", finding_data.get("remediation")),
            )
            db.add(finding)

        db.commit()
        db.refresh(scan)
                
        # --- Adaptive Learning: feed scan results with FULL details ---
        try:
            scan_findings = [
                {
                    "description": fd.get("description", ""),
                    "title": fd.get("title", ""),
                    "severity": fd.get("severity", "MEDIUM"),
                    "rule_id": fd.get("rule_id", ""),
                    "resource": fd.get("resource", ""),
                    "file_path": fd.get("file_path", file.filename),
                    "file": file.filename,
                    "scanner": fd.get("scanner", ""),
                    "category": fd.get("category", ""),
                    "line_number": fd.get("line_number"),
                    "code_snippet": fd.get("code_snippet", ""),
                    "remediation_steps": fd.get("remediation_steps"),
                    "remediation": fd.get("remediation", fd.get("llm_remediation", "")),
                }
                for fd in all_findings
            ]
            learning_engine.on_scan_completed(scan.id, scan_findings, risk_score)
        except Exception as learn_err:
            logger.debug("Adaptive learning hook error (non-fatal): %s", learn_err)

    except Exception as e:
        scan.status = ScanStatus.FAILED
        scan.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
    
    return scan


@app.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: int, db: Session = Depends(get_db)):
    """Get scan results by ID."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.get("/scans", response_model=List[ScanResponse])
async def list_scans(
    skip: int = 0,
    limit: int = 100,
    severity: str = None,
    scanner: str = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """List all scans with optional filtering by severity, scanner, and date range."""
    query = db.query(Scan).order_by(Scan.created_at.desc())
    
    # Apply filters if provided
    if start_date:
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Scan.created_at >= start)
        except (ValueError, TypeError):
            pass
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Scan.created_at <= end)
        except (ValueError, TypeError):
            pass
    
    # For severity/scanner filtering, we need to join with findings
    # This is simplified - a more complex query would be needed for exact filtering
    
    scans = query.offset(skip).limit(limit).all()
    return scans


@app.get("/scans/stats")
async def get_scan_statistics(db: Session = Depends(get_db)):
    """Get aggregated statistics across all scans."""
    from sqlalchemy import func
    
    # Total scans
    total_scans = db.query(func.count(Scan.id)).scalar()
    
    # Total findings by severity
    findings_by_severity = db.query(
        Finding.severity,
        func.count(Finding.id)
    ).group_by(Finding.severity).all()
    
    severity_counts = {sev: count for sev, count in findings_by_severity}
    
    # Findings by scanner type
    findings_by_scanner = db.query(
        Finding.scanner,
        func.count(Finding.id)
    ).filter(Finding.scanner.isnot(None)).group_by(Finding.scanner).all()
    
    scanner_counts = {scanner: count for scanner, count in findings_by_scanner}
    
    # Average scores
    avg_scores = db.query(
        func.avg(Scan.unified_risk_score).label('avg_risk'),
        func.avg(Scan.ml_score).label('avg_ml'),
        func.avg(Scan.rules_score).label('avg_rules'),
        func.avg(Scan.llm_score).label('avg_llm'),
        func.avg(Scan.secrets_score).label('avg_secrets'),
        func.avg(Scan.cve_score).label('avg_cve'),
        func.avg(Scan.compliance_score).label('avg_compliance')
    ).first()
    
    # Recent scans trend (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_scans = db.query(
        func.date(Scan.created_at).label('date'),
        func.count(Scan.id).label('count')
    ).filter(
        Scan.created_at >= thirty_days_ago
    ).group_by(
        func.date(Scan.created_at)
    ).order_by(func.date(Scan.created_at)).all()
    
    trend_data = [{"date": str(date), "count": count} for date, count in recent_scans]
    
    return {
        "total_scans": total_scans or 0,
        "findings_by_severity": {
            "CRITICAL": severity_counts.get("CRITICAL", 0),
            "HIGH": severity_counts.get("HIGH", 0),
            "MEDIUM": severity_counts.get("MEDIUM", 0),
            "LOW": severity_counts.get("LOW", 0),
            "INFO": severity_counts.get("INFO", 0)
        },
        "findings_by_scanner": {
            "ML": scanner_counts.get("ML", 0),
            "Rules": scanner_counts.get("Rules", 0),
            "LLM": scanner_counts.get("LLM", 0),
            "Secrets": scanner_counts.get("Secrets", 0),
            "CVE": scanner_counts.get("CVE", 0),
            "Compliance": scanner_counts.get("Compliance", 0)
        },
        "average_scores": {
            "unified_risk": float(avg_scores.avg_risk) if avg_scores.avg_risk else 0.0,
            "ml_score": float(avg_scores.avg_ml) if avg_scores.avg_ml else 0.0,
            "rules_score": float(avg_scores.avg_rules) if avg_scores.avg_rules else 0.0,
            "llm_score": float(avg_scores.avg_llm) if avg_scores.avg_llm else 0.0,
            "secrets_score": float(avg_scores.avg_secrets) if avg_scores.avg_secrets else 0.0,
            "cve_score": float(avg_scores.avg_cve) if avg_scores.avg_cve else 0.0,
            "compliance_score": float(avg_scores.avg_compliance) if avg_scores.avg_compliance else 0.0
        },
        "trend_30_days": trend_data
    }


@app.delete("/scans/{scan_id}")
async def delete_scan(scan_id: int, db: Session = Depends(get_db), user: AuthUser = Depends(optional_auth)):
    """Delete a scan and all associated findings."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Delete associated findings first
    db.query(Finding).filter(Finding.scan_id == scan_id).delete()
    
    # Delete the scan
    db.delete(scan)
    db.commit()
    
    return {"message": f"Scan {scan_id} deleted successfully"}


@app.get("/findings/{finding_id}/duplicates")
async def get_duplicate_findings(finding_id: int, db: Session = Depends(get_db)):
    """Get all duplicate occurrences of a finding."""
    from app.database import DatabaseService
    
    # Get the original finding
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    if not finding.finding_hash:
        return {
            "finding_id": finding_id,
            "duplicates": [],
            "total_occurrences": 1
        }
    
    # Get all findings with the same hash
    db_service = DatabaseService(db)
    duplicates = db_service.get_duplicate_findings(finding.finding_hash, limit=50)
    
    return {
        "finding_id": finding_id,
        "finding_hash": finding.finding_hash,
        "duplicates": [
            {
                "id": f.id,
                "scan_id": f.scan_id,
                "first_seen": f.first_seen,
                "last_seen": f.last_seen,
                "occurrence_count": f.occurrence_count,
                "severity": f.severity,
                "is_suppressed": f.is_suppressed
            }
            for f in duplicates
        ],
        "total_occurrences": sum(f.occurrence_count for f in duplicates)
    }


@app.post("/findings/{finding_id}/suppress")
async def suppress_finding(finding_id: int, db: Session = Depends(get_db), user: AuthUser = Depends(optional_auth)):
    """Suppress a finding to prevent it from appearing in future deduplication."""
    from app.database import DatabaseService
    
    db_service = DatabaseService(db)
    finding = db_service.suppress_finding(finding_id)
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    return {
        "message": f"Finding {finding_id} suppressed",
        "finding_id": finding_id,
        "is_suppressed": finding.is_suppressed
    }


@app.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submit feedback for a scan or finding.
    Used for online learning and model improvement.
    """
    # Validate scan exists
    scan = db.query(Scan).filter(Scan.id == feedback.scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Validate finding if provided
    if feedback.finding_id:
        finding = db.query(Finding).filter(Finding.id == feedback.finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
    
    # Create feedback — persist all available fields
    db_feedback = Feedback(
        scan_id=feedback.scan_id,
        finding_id=feedback.finding_id,
        is_correct=feedback.is_correct,
        adjusted_severity=feedback.adjusted_severity,
        user_comment=feedback.user_comment,
        scanner_type=getattr(feedback, 'scanner_type', None),
        feedback_type=getattr(feedback, 'feedback_type', None),
        model_version=getattr(feedback, 'model_version', None),
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    # --- Adaptive Learning: feed every feedback event ---
    try:
        # Resolve the rule_id from the finding if available
        rule_id = None
        if feedback.finding_id:
            finding_obj = db.query(Finding).filter(Finding.id == feedback.finding_id).first()
            if finding_obj:
                rule_id = finding_obj.rule_id

        learning_engine.on_feedback_received(
            scan_id=scan.id,
            file_content=scan.file_content or "",
            filename=scan.filename or "",
            is_correct=feedback.is_correct,
            feedback_type=getattr(feedback, 'feedback_type', None),
            scan_risk_score=scan.risk_score or 0.0,
            rule_id=rule_id,
        )

        # Check if auto-retrain should fire
        should_retrain, reason = learning_engine.should_auto_retrain()
        if should_retrain:
            logger.info("🔄 Auto-retraining triggered: %s", reason)
            try:
                enqueue_retrain_job()
                learning_engine.on_retrain_completed({"trigger": reason})
            except Exception as retrain_err:
                logger.warning("Auto-retrain enqueue failed: %s", retrain_err)
    except Exception as learn_err:
        logger.debug("Adaptive learning feedback hook error (non-fatal): %s", learn_err)

    return db_feedback


@app.get("/feedback", response_model=List[FeedbackResponse])
async def list_feedback(
    skip: int = 0,
    limit: int = 100,
    scanner: str = None,  # Filter by scanner type
    db: Session = Depends(get_db)
):
    """List all feedback with optional scanner filtering."""
    query = db.query(Feedback).order_by(Feedback.created_at.desc())
    
    if scanner:
        query = query.filter(Feedback.scanner_type == scanner)
    
    feedbacks = query.offset(skip).limit(limit).all()
    return feedbacks


@app.get("/feedback/stats")
async def get_feedback_statistics(db: Session = Depends(get_db)):
    """Get aggregated feedback statistics by scanner type."""
    from sqlalchemy import func
    
    # Feedback by scanner type
    feedback_by_scanner = db.query(
        Feedback.scanner_type,
        func.count(Feedback.id).label('total'),
        func.sum(sa_case((Feedback.feedback_type == 'accurate', 1), else_=0)).label('accurate'),
        func.sum(sa_case((Feedback.feedback_type == 'false_positive', 1), else_=0)).label('false_positives'),
        func.sum(sa_case((Feedback.feedback_type == 'false_negative', 1), else_=0)).label('false_negatives')
    ).filter(
        Feedback.scanner_type.isnot(None)
    ).group_by(Feedback.scanner_type).all()
    
    scanner_stats = {}
    for scanner, total, accurate, fp, fn in feedback_by_scanner:
        accuracy = (accurate / total * 100) if total > 0 else 0
        scanner_stats[scanner] = {
            'total_feedback': total,
            'accurate': accurate or 0,
            'false_positives': fp or 0,
            'false_negatives': fn or 0,
            'accuracy_percentage': round(accuracy, 2)
        }
    
    return {
        'by_scanner': scanner_stats,
        'total_feedback': sum(s['total_feedback'] for s in scanner_stats.values())
    }


@app.get("/model/status", response_model=ModelStatusResponse)
async def get_model_status(db: Session = Depends(get_db)):
    """Get current model status and metrics."""
    # Get active model
    active_model = db.query(ModelVersion).filter(ModelVersion.is_active == 1).first()
    
    # Get statistics
    total_scans = db.query(Scan).count()
    total_feedback = db.query(Feedback).count()
    pending_feedback = db.query(Feedback).filter(Feedback.is_correct.isnot(None)).count()
    
    if active_model:
        return ModelStatusResponse(
            active_version=active_model.version,
            model_type=active_model.model_type,
            accuracy=active_model.accuracy,
            precision=active_model.precision,
            recall=active_model.recall,
            f1_score=active_model.f1_score,
            training_samples=active_model.training_samples,
            created_at=active_model.created_at,
            total_scans=total_scans,
            total_feedback=total_feedback,
            pending_retraining_samples=pending_feedback
        )
    
    return ModelStatusResponse(
        total_scans=total_scans,
        total_feedback=total_feedback,
        pending_retraining_samples=pending_feedback
    )


@app.post("/model/retrain", response_model=JobResponse)
async def retrain_model(
    request: RetrainRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger model retraining with new feedback data.
    Uses online learning with SGDClassifier.
    """
    # Check if enough feedback
    feedback_count = db.query(Feedback).filter(Feedback.is_correct.isnot(None)).count()
    
    if not request.force and feedback_count < request.min_samples:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough feedback for retraining. "
                   f"Need {request.min_samples}, have {feedback_count}. "
                   f"Use force=true to override."
        )
    
    # Enqueue retrain job
    job = enqueue_retrain_job()
    
    return JobResponse(
        job_id=job.id,
        status="queued",
        message=f"Retraining job queued with {feedback_count} samples"
    )


@app.get("/model/versions", response_model=List[ModelStatusResponse])
async def list_model_versions(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List all model versions."""
    versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        ModelStatusResponse(
            active_version=v.version,
            model_type=v.model_type,
            accuracy=v.accuracy,
            precision=v.precision,
            recall=v.recall,
            f1_score=v.f1_score,
            training_samples=v.training_samples,
            created_at=v.created_at
        )
        for v in versions
    ]


# ---------------------------------------------------------------------------
# Adaptive Learning Endpoints
# ---------------------------------------------------------------------------

@app.get("/learning/status")
async def get_learning_status():
    """
    Full status of the adaptive learning engine — drift detection,
    pattern discovery, rule weights, training buffer, auto-retrain state.
    """
    return learning_engine.get_learning_status()


@app.get("/learning/patterns")
async def get_discovered_patterns():
    """Return all discovered vulnerability patterns and auto-generated rules."""
    return learning_engine.pattern_engine.get_stats()


@app.get("/learning/patterns/{signature}")
async def get_pattern_detail(signature: str):
    """Return full details for a specific discovered pattern."""
    detail = learning_engine.pattern_engine.get_pattern_detail(signature)
    if detail is None:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return detail


@app.get("/learning/drift")
async def get_drift_status():
    """Current model drift status (PSI-based)."""
    return learning_engine.drift_detector.check()


@app.get("/learning/rule-weights")
async def get_rule_weights():
    """Adaptive rule confidence weights based on feedback history."""
    return learning_engine.rule_weights.get_stats()


@app.get("/learning/telemetry")
async def get_learning_telemetry(limit: int = 50):
    """Recent learning events for audit / debugging."""
    return {
        "summary": learning_engine.telemetry.get_summary(),
        "recent_events": learning_engine.telemetry.get_recent(limit),
    }


@app.post("/learning/discover")
async def trigger_pattern_discovery():
    """Manually trigger a pattern discovery cycle."""
    result = learning_engine.pattern_engine.run_discovery_cycle()
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
