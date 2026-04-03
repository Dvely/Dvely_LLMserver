from typing import Optional

from fastapi import Header, Request

from app.core.config import get_settings
from app.core.errors import APIError


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


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


async def verify_api_key_anthropic(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None, alias="x-api-key"),
) -> None:
    _ = request
    token = _extract_bearer_token(authorization)
    candidate = x_api_key or token
    if not _is_valid_api_key(candidate):
        raise APIError(401, "authentication_error", "Invalid or missing API key")
