"""
Observability middleware and utilities for CloudGuard AI services
"""
import time
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for request ID
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to all requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(request_id)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class TimingMiddleware(BaseHTTPMiddleware):
    """Log request timing and status"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = request_id_ctx.get()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            log_request(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2)
            )
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration * 1000, 2)
            )
            raise

def get_request_id() -> Optional[str]:
    """Get current request ID from context"""
    return request_id_ctx.get()

def log_request(request_id: str, method: str, path: str, status_code: int, duration_ms: float):
    """Log request with structured format"""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "type": "request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms
    }
    logging.info(json.dumps(log_data))

def log_error(request_id: str, method: str, path: str, error: str, duration_ms: float):
    """Log error with structured format"""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "type": "error",
        "method": method,
        "path": path,
        "error": error,
        "duration_ms": duration_ms
    }
    logging.error(json.dumps(log_data))

def log_operation(operation: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None):
    """Log internal operation timing"""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": get_request_id(),
        "type": "operation",
        "operation": operation,
        "duration_ms": duration_ms
    }
    if metadata:
        log_data.update(metadata)
    logging.info(json.dumps(log_data))

class OperationTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.metadata = metadata or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is not None:
            self.metadata["error"] = str(exc_val)
        log_operation(self.operation, round(duration * 1000, 2), self.metadata)
        return False

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)
