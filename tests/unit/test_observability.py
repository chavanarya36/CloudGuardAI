"""Unit tests for observability middleware and logging"""
import pytest
import json
from fastapi import FastAPI
from starlette.testclient import TestClient
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add api to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "api"))


def test_request_id_middleware_adds_header():
    """Test that RequestIDMiddleware adds X-Request-ID header"""
    from app.observability import RequestIDMiddleware
    
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    with TestClient(app) as client:
        response = client.get("/test")
    
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0  # Non-empty request ID


def test_request_id_middleware_preserves_existing():
    """Test that RequestIDMiddleware preserves existing request ID"""
    from app.observability import RequestIDMiddleware
    
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    with TestClient(app) as client:
        existing_id = "test-request-id-12345"
        response = client.get("/test", headers={"X-Request-ID": existing_id})
    
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == existing_id


def test_timing_middleware_logs_duration(caplog):
    """Test that TimingMiddleware logs request duration"""
    from app.observability import TimingMiddleware, RequestIDMiddleware
    import logging
    
    caplog.set_level(logging.INFO)
    
    app = FastAPI()
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        import asyncio
        await asyncio.sleep(0.05)  # Simulate work
        return {"status": "ok"}
    
    with TestClient(app) as client:
        response = client.get("/test")
    
    assert response.status_code == 200
    
    # Check logs contain timing information (JSON format)
    log_records = [record.message for record in caplog.records]
    # Parse JSON logs
    request_logs = []
    for log in log_records:
        try:
            data = json.loads(log)
            if data.get('type') == 'request':
                request_logs.append(data)
        except:
            pass
    
    assert len(request_logs) > 0
    log_data = request_logs[0]
    assert log_data['method'] == 'GET'
    assert log_data['path'] == '/test'
    assert 'duration_ms' in log_data
    assert log_data['duration_ms'] > 0


def test_timing_middleware_logs_status_code(caplog):
    """Test that TimingMiddleware logs status code"""
    from app.observability import TimingMiddleware
    import logging
    
    caplog.set_level(logging.INFO)
    
    app = FastAPI()
    app.add_middleware(TimingMiddleware)
    
    @app.get("/success")
    async def success_endpoint():
        return {"status": "ok"}
    
    @app.get("/error")
    async def error_endpoint():
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Test error")
    
    with TestClient(app) as client:
        # Test successful request
        client.get("/success")
        success_logs = [r.message for r in caplog.records if "200" in r.message]
        assert len(success_logs) > 0
        
        # Test error request
        try:
            client.get("/error")
        except:
            pass
        error_logs = [r.message for r in caplog.records if "500" in r.message]
        assert len(error_logs) > 0


def test_operation_timer_context_manager(caplog):
    """Test OperationTimer context manager"""
    from app.observability import OperationTimer
    import logging
    import time
    
    caplog.set_level(logging.INFO)
    
    with OperationTimer("test_operation"):
        time.sleep(0.05)
    
    # Check logs (JSON format)
    log_messages = [record.message for record in caplog.records]
    operation_logs = []
    for log in log_messages:
        try:
            data = json.loads(log)
            if data.get('operation') == 'test_operation':
                operation_logs.append(data)
        except:
            pass
    
    assert len(operation_logs) > 0
    log_data = operation_logs[0]
    assert log_data['type'] == 'operation'
    assert 'duration_ms' in log_data
    assert log_data['duration_ms'] > 0


def test_log_request_function(caplog):
    """Test log_request helper function"""
    from app.observability import log_request
    import logging
    
    caplog.set_level(logging.INFO)
    
    log_request(
        request_id="request-123",
        method="GET",
        path="/api/scan",
        status_code=200,
        duration_ms=150.5
    )
    
    assert len(caplog.records) > 0
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    assert log_data['method'] == 'GET'
    assert log_data['path'] == '/api/scan'
    assert log_data['status_code'] == 200
    assert log_data['request_id'] == 'request-123'
    assert log_data['duration_ms'] == 150.5


def test_log_error_function(caplog):
    """Test log_error helper function"""
    from app.observability import log_error
    import logging
    
    caplog.set_level(logging.ERROR)
    
    log_error(
        request_id="request-123",
        method="POST",
        path="/api/test",
        error="Test error message",
        duration_ms=100.0
    )
    
    assert len(caplog.records) > 0
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    assert log_data['type'] == 'error'
    assert log_data['error'] == 'Test error message'
    assert log_data['request_id'] == 'request-123'


def test_log_operation_function(caplog):
    """Test log_operation helper function"""
    from app.observability import log_operation
    import logging
    
    caplog.set_level(logging.INFO)
    
    log_operation("database_query", 45.2, {"rows": 10})
    
    assert len(caplog.records) > 0
    log_message = caplog.records[0].message
    log_data = json.loads(log_message)
    
    assert log_data['operation'] == 'database_query'
    assert log_data['duration_ms'] == 45.2
    assert log_data['rows'] == 10


def test_request_id_in_context():
    """Test that request_id is available in context"""
    from app.observability import RequestIDMiddleware, request_id_ctx
    
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    captured_id = None
    
    @app.get("/test")
    async def test_endpoint():
        nonlocal captured_id
        captured_id = request_id_ctx.get()
        return {"status": "ok"}
    
    with TestClient(app) as client:
        response = client.get("/test")
    
    assert response.status_code == 200
    assert captured_id is not None
    assert captured_id == response.headers["X-Request-ID"]


def test_middleware_combination(caplog):
    """Test RequestIDMiddleware and TimingMiddleware work together"""
    from app.observability import RequestIDMiddleware, TimingMiddleware
    import logging
    
    caplog.set_level(logging.INFO)
    
    app = FastAPI()
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    with TestClient(app) as client:
        response = client.get("/test")
    
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    
    # Check that timing log includes request (JSON format)
    log_messages = [record.message for record in caplog.records]
    request_logs = []
    for log in log_messages:
        try:
            data = json.loads(log)
            if data.get('type') == 'request':
                request_logs.append(data)
        except:
            pass
    
    assert len(request_logs) > 0
    assert request_logs[0]['method'] == 'GET'
    assert request_logs[0]['path'] == '/test'


def test_operation_timer_with_exception(caplog):
    """Test OperationTimer logs even when exception occurs"""
    from app.observability import OperationTimer
    import logging
    
    caplog.set_level(logging.INFO)
    
    try:
        with OperationTimer("failing_operation"):
            raise ValueError("Test error")
    except ValueError:
        pass
    
    # Timer should still log
    log_messages = [record.message for record in caplog.records]
    operation_logs = [log for log in log_messages if "failing_operation" in log]
    
    assert len(operation_logs) > 0


def test_structured_logging_format(caplog):
    """Test that logs are in structured JSON format"""
    from app.observability import log_request
    import logging
    
    caplog.set_level(logging.INFO)
    
    log_request("POST", "/scan", 200, 123.45, "req-789")
    
    # Log message should contain key information
    assert len(caplog.records) > 0
    log_message = caplog.records[0].message
    
    # Should contain structured data
    assert "POST" in log_message
    assert "/scan" in log_message
    assert "200" in log_message
    assert "req-789" in log_message


def test_timing_middleware_measures_actual_duration(caplog):
    """Test that TimingMiddleware measures actual request duration"""
    from app.observability import TimingMiddleware
    import logging
    import asyncio
    
    caplog.set_level(logging.INFO)
    
    app = FastAPI()
    app.add_middleware(TimingMiddleware)
    
    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(0.2)  # 200ms
        return {"status": "ok"}
    
    with TestClient(app) as client:
        response = client.get("/slow")
    
    assert response.status_code == 200
    
    # Find timing log with JSON parsing
    import json
    timing_logs = []
    for record in caplog.records:
        try:
            log_data = json.loads(record.message)
            if log_data.get("type") == "request" and log_data.get("status_code") == 200:
                timing_logs.append(log_data)
        except (json.JSONDecodeError, AttributeError):
            continue
    
    assert len(timing_logs) > 0
    assert timing_logs[0]["duration_ms"] > 200
