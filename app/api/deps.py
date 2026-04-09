from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    """
    Enforce API key authentication on every request.

    Fail-safe by default: if KTRT_API_KEY is not configured the service
    denies all requests rather than falling open. This prevents an
    accidentally un-keyed production deployment from being publicly
    accessible.

    To enable open access for local development, set KTRT_API_KEY to the
    literal string "dev" and pass that same value in the X-API-Key header.
    """
    if not settings.ktrt_api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "KTRT_API_KEY is not configured. "
                "Set it in your environment before starting the service."
            ),
        )
    if api_key != settings.ktrt_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return api_key
