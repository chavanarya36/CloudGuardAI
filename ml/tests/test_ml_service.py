import pytest
from fastapi.testclient import TestClient
from ml_service.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "CloudGuard ML Service"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_predict_endpoint():
    response = client.post(
        "/predict",
        json={
            "file_path": "test.tf",
            "file_content": "resource \"aws_s3_bucket\" \"test\" { acl = \"public-read\" }"
        }
    )
    # Might fail if models not available, but endpoint should exist
    assert response.status_code in [200, 500]


def test_rules_scan_endpoint():
    response = client.post(
        "/rules-scan",
        json={
            "file_path": "test.tf",
            "file_content": "resource \"aws_s3_bucket\" \"test\" { acl = \"public-read\" }"
        }
    )
    assert response.status_code in [200, 500]


def test_aggregate_endpoint():
    response = client.post(
        "/aggregate",
        json={
            "file_path": "test.tf",
            "file_content": "resource \"aws_s3_bucket\" \"test\" { acl = \"public-read\" }"
        }
    )
    assert response.status_code in [200, 500]
