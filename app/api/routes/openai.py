from typing import Any

from fastapi import APIRouter, Depends, Request
from sse_starlette import EventSourceResponse

from app.core.logging import get_logger
from app.core.security import verify_api_key_openai
from app.schemas.openai import OpenAIChatCompletionRequest, OpenAIChatCompletionResponse
from app.services.response_mapper import map_ollama_to_openai_response
from app.services.streaming import map_openai_stream

router = APIRouter(tags=["openai"])
logger = get_logger("gateway.openai")


def _build_ollama_payload(request: Request, raw_model: str, body: OpenAIChatCompletionRequest) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if body.temperature is not None:
        options["temperature"] = body.temperature
    if body.top_p is not None:
        options["top_p"] = body.top_p
    if body.max_tokens is not None:
        options["num_predict"] = body.max_tokens

    settings = request.app.state.settings
    payload: dict[str, Any] = {
        "model": raw_model,
        "messages": [m.model_dump() for m in body.messages],
        "stream": body.stream,
        "keep_alive": settings.ollama_keep_alive,
    }
    if options:
        payload["options"] = options

    return payload


@router.post("/v1/chat/completions", response_model=OpenAIChatCompletionResponse)
async def chat_completions(
    request: Request,
    body: OpenAIChatCompletionRequest,
    _: None = Depends(verify_api_key_openai),
):
    registry = request.app.state.model_registry
    ollama_client = request.app.state.ollama_client

    raw_model = registry.resolve(body.model)
    logger.info("model_selected alias=%s upstream=%s", body.model, raw_model)

    payload = _build_ollama_payload(request, raw_model, body)

    if body.stream:
        upstream_stream = ollama_client.stream_chat(payload)
        return EventSourceResponse(map_openai_stream(body.model, upstream_stream), media_type="text/event-stream")

    ollama_response = await ollama_client.chat(payload)
    return map_ollama_to_openai_response(body.model, ollama_response)
