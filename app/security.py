import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER_NAME = "X-API-Key"
_api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
_expected_api_key = os.getenv("API_KEY", "dev-api-key")


def require_api_key(api_key: Optional[str] = Depends(_api_key_header)) -> str:
    if api_key != _expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
