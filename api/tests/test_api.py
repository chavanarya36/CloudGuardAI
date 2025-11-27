import pytest
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
