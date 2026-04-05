from typing import Optional

from fastapi import Header, Request

from app.core.config import get_settings
from app.core.errors import APIError


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    value = authorization.strip()
    if not value:
        return None

    parts = value.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1].strip()
        return token or None

    # Accept raw API keys as-is for Swagger docs manual header input.
    return value


def _is_valid_api_key(api_key: Optional[str]) -> bool:
    settings = get_settings()
    return bool(api_key) and api_key in settings.api_keys


async def verify_api_key_openai(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> None:
    _ = request
    token = _extract_bearer_token(authorization)
    if not _is_valid_api_key(token):
        raise APIError(401, "authentication_error", "Invalid or missing API key")
