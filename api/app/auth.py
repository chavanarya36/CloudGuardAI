"""
Authentication & Authorization middleware for CloudGuard AI API.

Supports two modes:
1. API Key authentication (header: X-API-Key)
2. JWT Bearer token authentication (header: Authorization: Bearer <token>)

In development mode (DEBUG=true), authentication is optional.
"""

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    sub: str  # subject (user or service name)
    exp: float  # expiry timestamp
    iat: float  # issued at
    scopes: list[str] = ["read", "write"]


class AuthUser(BaseModel):
    """Authenticated user/service identity."""
    identity: str
    auth_method: str  # "api_key" | "jwt" | "dev_bypass"
    scopes: list[str] = ["read", "write"]


# ---------------------------------------------------------------------------
# JWT helpers (HMAC-SHA256 based — no external dependency)
# ---------------------------------------------------------------------------

def _b64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    import base64
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def create_jwt(subject: str, scopes: list[str] | None = None, expires_minutes: int = 60) -> str:
    """Create a signed JWT token."""
    now = time.time()
    payload = TokenPayload(
        sub=subject,
        exp=now + expires_minutes * 60,
        iat=now,
        scopes=scopes or ["read", "write"],
    )
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url_encode(payload.model_dump_json().encode())
    signing_input = f"{header}.{body}"
    signature = hmac.new(settings.secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def verify_jwt(token: str) -> TokenPayload:
    """Verify and decode a JWT token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    signing_input = f"{parts[0]}.{parts[1]}"
    expected_sig = hmac.new(settings.secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
    actual_sig = _b64url_decode(parts[2])

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid signature")

    payload_data = json.loads(_b64url_decode(parts[1]))
    payload = TokenPayload(**payload_data)

    if payload.exp < time.time():
        raise ValueError("Token expired")

    return payload


# ---------------------------------------------------------------------------
# API Key management
# ---------------------------------------------------------------------------

# In production, store hashed keys in the database.
# For now, support a configurable master key + dev mode.
_VALID_API_KEYS: set[str] = set()


def generate_api_key() -> str:
    """Generate a new random API key."""
    key = f"cg_{secrets.token_urlsafe(32)}"
    _VALID_API_KEYS.add(key)
    return key


def _is_valid_api_key(key: str) -> bool:
    """Check if an API key is valid."""
    # Accept the configured secret key as a master API key
    if hmac.compare_digest(key, settings.secret_key):
        return True
    return key in _VALID_API_KEYS


# ---------------------------------------------------------------------------
# Dependency — use in FastAPI endpoints
# ---------------------------------------------------------------------------

async def get_current_user(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> AuthUser:
    """
    Authenticate the request via API key or JWT.

    In debug/dev mode, unauthenticated requests are allowed with limited scope.
    """
    # 1. Try API key
    if api_key:
        if _is_valid_api_key(api_key):
            return AuthUser(identity="api_key_user", auth_method="api_key")
        raise HTTPException(status_code=401, detail="Invalid API key")

    # 2. Try Bearer JWT
    if bearer:
        try:
            payload = verify_jwt(bearer.credentials)
            return AuthUser(identity=payload.sub, auth_method="jwt", scopes=payload.scopes)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # 3. Dev/debug bypass — allow unauthenticated in development
    if settings.debug:
        return AuthUser(identity="dev_user", auth_method="dev_bypass")

    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide X-API-Key header or Bearer token.",
    )


async def optional_auth(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> Optional[AuthUser]:
    """Optional authentication — returns None if no credentials provided."""
    try:
        return await get_current_user(request, api_key, bearer)
    except HTTPException:
        return None
