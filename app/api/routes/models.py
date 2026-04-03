from fastapi import APIRouter, Depends, Request

from app.core.security import verify_api_key_openai
from app.schemas.common import ModelInfo, ModelListResponse

router = APIRouter(tags=["models"])


@router.get("/v1/models", response_model=ModelListResponse)
async def list_models(
    request: Request,
    _: None = Depends(verify_api_key_openai),
) -> ModelListResponse:
    aliases = request.app.state.model_registry.aliases()
    return ModelListResponse(data=[ModelInfo(id=alias) for alias in aliases])
