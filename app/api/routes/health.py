from fastapi import APIRouter, Request

from app.core.errors import APIError

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> dict:
    ready = await request.app.state.ollama_client.check_ready()
    if not ready:
        raise APIError(503, "service_unavailable", "Ollama is unavailable")
    return {"status": "ready"}
