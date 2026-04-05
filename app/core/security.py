from typing import Optional

from fastapi import Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.errors import APIError


http_bearer = HTTPBearer(auto_error=False)


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
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer),
) -> None:
    _ = request
    token = None
    if credentials:
        # HTTPBearer returns scheme/token separately and Swagger Authorize sets this path.
        if credentials.scheme and credentials.scheme.lower() == "bearer":
            token = credentials.credentials.strip() if credentials.credentials else None
        elif credentials.credentials:
            # Be tolerant to non-standard cases.
            token = _extract_bearer_token(f"{credentials.scheme} {credentials.credentials}")

    if not token:
        token = _extract_bearer_token(request.headers.get("Authorization"))

    if not _is_valid_api_key(token):
        raise APIError(401, "authentication_error", "Invalid or missing API key")
