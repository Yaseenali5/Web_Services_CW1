import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer_scheme = HTTPBearer(auto_error=False)
_token_secret = os.getenv("TOKEN_SECRET", "dev-token-secret-change-me")
_token_ttl_seconds = int(os.getenv("TOKEN_TTL_SECONDS", "3600"))

# Demo users for coursework presentation. Use env vars in real deployments.
_demo_users = {
    os.getenv("ADMIN_USERNAME", "admin"): {
        "password": os.getenv("ADMIN_PASSWORD", "adminpass"),
        "role": "admin",
        "scopes": ["read", "write"],
    },
    os.getenv("VIEWER_USERNAME", "viewer"): {
        "password": os.getenv("VIEWER_PASSWORD", "viewerpass"),
        "role": "viewer",
        "scopes": ["read"],
    },
}


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: bytes) -> str:
    signature = hmac.new(_token_secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(signature)


def create_access_token(subject: str, role: str, scopes: list[str], ttl_seconds: Optional[int] = None) -> str:
    now = int(time.time())
    ttl = _token_ttl_seconds if ttl_seconds is None else ttl_seconds
    payload = {
        "sub": subject,
        "role": role,
        "scopes": scopes,
        "iat": now,
        "exp": now + ttl,
    }

    header_raw = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8"))
    payload_raw = _b64url_encode(json.dumps(payload).encode("utf-8"))
    message = f"{header_raw}.{payload_raw}".encode("utf-8")
    signature = _sign(message)
    return f"{header_raw}.{payload_raw}.{signature}"


def decode_and_verify_token(token: str) -> dict:
    try:
        header_raw, payload_raw, signature = token.split(".")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

    message = f"{header_raw}.{payload_raw}".encode("utf-8")
    expected = _sign(message)
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")

    try:
        payload = json.loads(_b64url_decode(payload_raw).decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    return payload


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = _demo_users.get(username)
    if not user:
        return None
    if password != user["password"]:
        return None
    return {
        "username": username,
        "role": user["role"],
        "scopes": user["scopes"],
    }


def get_current_principal(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    return decode_and_verify_token(credentials.credentials)


def require_write_access(principal: dict = Depends(get_current_principal)) -> dict:
    scopes = principal.get("scopes", [])
    if "write" not in scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope for write operations")
    return principal
