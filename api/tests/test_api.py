import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


# ---------------------------------------------------------------------------
# Basic endpoint tests
# ---------------------------------------------------------------------------

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "CloudGuard AI API"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_model_status():
    response = client.get("/model/status")
    assert response.status_code == 200
    data = response.json()
    assert "total_scans" in data
    assert "total_feedback" in data


def test_list_scans_empty():
    response = client.get("/scans")
    assert response.status_code == 200
    assert response.json() == []


def test_list_feedback_empty():
    response = client.get("/feedback")
    assert response.status_code == 200
    assert response.json() == []


def test_get_scan_not_found():
    response = client.get("/scan/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Scan upload tests
# ---------------------------------------------------------------------------

SAMPLE_TERRAFORM = """
resource "aws_s3_bucket" "data" {
  bucket = "my-bucket"
  acl    = "public-read"
}
""".strip()


def _upload_scan(content: str = SAMPLE_TERRAFORM, filename: str = "main.tf", scan_mode: str = "all"):
    """Helper: upload a file for scanning and return the response."""
    return client.post(
        "/scan",
        files={"file": (filename, io.BytesIO(content.encode()), "application/octet-stream")},
        data={"scan_mode": scan_mode},
    )


def test_scan_upload_success():
    """POST /scan returns 200 with expected result shape."""
    resp = _upload_scan()
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["filename"] == "main.tf"
    assert data["status"] in ("completed", "COMPLETED")
    assert "risk_score" in data


def test_scan_upload_creates_record():
    """After uploading, the scan appears in GET /scans."""
    _upload_scan()
    scans = client.get("/scans").json()
    assert len(scans) >= 1
    assert scans[0]["filename"] == "main.tf"


def test_scan_get_by_id():
    """GET /scan/:id returns the created scan."""
    scan_id = _upload_scan().json()["id"]
    resp = client.get(f"/scan/{scan_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == scan_id


def test_scan_mode_gnn():
    """Scan with mode 'gnn' completes (falls back to integrated scanner)."""
    resp = _upload_scan(scan_mode="gnn")
    assert resp.status_code == 200


def test_scan_mode_checkov():
    """Scan with mode 'checkov' completes."""
    resp = _upload_scan(scan_mode="checkov")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Scan stats tests
# ---------------------------------------------------------------------------

def test_scan_stats_empty():
    """GET /scans/stats works with no data."""
    resp = client.get("/scans/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_scans"] == 0
    assert "findings_by_severity" in data
    assert "findings_by_scanner" in data
    assert "average_scores" in data


def test_scan_stats_after_upload():
    """Stats reflect a completed scan."""
    _upload_scan()
    data = client.get("/scans/stats").json()
    assert data["total_scans"] >= 1


# ---------------------------------------------------------------------------
# Delete scan tests
# ---------------------------------------------------------------------------

def test_delete_scan():
    """DELETE /scans/:id removes the scan."""
    scan_id = _upload_scan().json()["id"]
    resp = client.delete(f"/scans/{scan_id}")
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"].lower()
    # Confirm gone
    assert client.get(f"/scan/{scan_id}").status_code == 404


def test_delete_scan_not_found():
    """DELETE /scans/999 returns 404."""
    resp = client.delete("/scans/999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Feedback tests
# ---------------------------------------------------------------------------

def test_feedback_submit():
    """POST /feedback stores feedback for a valid scan."""
    scan_id = _upload_scan().json()["id"]
    resp = client.post("/feedback", json={
        "scan_id": scan_id,
        "is_correct": 1,
        "user_comment": "Looks accurate",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["scan_id"] == scan_id
    assert data["is_correct"] == 1


def test_feedback_invalid_scan():
    """Feedback for non-existent scan returns 404."""
    resp = client.post("/feedback", json={"scan_id": 9999, "is_correct": 1})
    assert resp.status_code == 404


def test_feedback_list_after_submit():
    """GET /feedback shows submitted feedback."""
    scan_id = _upload_scan().json()["id"]
    client.post("/feedback", json={"scan_id": scan_id, "is_correct": 0, "user_comment": "FP"})
    feedbacks = client.get("/feedback").json()
    assert len(feedbacks) >= 1
    assert feedbacks[0]["user_comment"] == "FP"


def test_feedback_stats():
    """GET /feedback/stats returns aggregated stats."""
    resp = client.get("/feedback/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_feedback" in data


# ---------------------------------------------------------------------------
# Model versions tests
# ---------------------------------------------------------------------------

def test_model_versions_empty():
    """GET /model/versions returns empty list initially."""
    resp = client.get("/model/versions")
    assert resp.status_code == 200
    assert resp.json() == []
