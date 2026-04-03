from typing import Any

from fastapi import APIRouter, Depends, Request
from sse_starlette import EventSourceResponse

from app.core.logging import get_logger
from app.core.security import verify_api_key_anthropic
from app.schemas.anthropic import AnthropicMessageRequest, AnthropicMessageResponse
from app.services.response_mapper import map_ollama_to_anthropic_response
from app.services.streaming import map_anthropic_stream

router = APIRouter(tags=["anthropic"])
logger = get_logger("gateway.anthropic")


def _anthropic_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(str(item.get("text", "")))
            elif hasattr(item, "type") and getattr(item, "type", None) == "text":
                texts.append(str(getattr(item, "text", "")))
        return "\n".join(texts)
    return ""


def _build_ollama_payload(request: Request, raw_model: str, body: AnthropicMessageRequest) -> dict[str, Any]:
    messages: list[dict[str, str]] = []

    if body.system:
        messages.append({"role": "system", "content": body.system})

    for msg in body.messages:
        messages.append(
            {
                "role": msg.role,
                "content": _anthropic_content_to_text(msg.content),
            }
        )

    options: dict[str, Any] = {}
    if body.max_tokens is not None:
        options["num_predict"] = body.max_tokens

    settings = request.app.state.settings
    payload: dict[str, Any] = {
        "model": raw_model,
        "messages": messages,
        "stream": body.stream,
        "keep_alive": settings.ollama_keep_alive,
    }
    if options:
        payload["options"] = options

    return payload


@router.post("/v1/messages", response_model=AnthropicMessageResponse)
async def create_message(
    request: Request,
    body: AnthropicMessageRequest,
    _: None = Depends(verify_api_key_anthropic),
):
    registry = request.app.state.model_registry
    ollama_client = request.app.state.ollama_client

    raw_model = registry.resolve(body.model)
    logger.info("model_selected alias=%s upstream=%s", body.model, raw_model)

    payload = _build_ollama_payload(request, raw_model, body)

    if body.stream:
        upstream_stream = ollama_client.stream_chat(payload)
        return EventSourceResponse(map_anthropic_stream(body.model, upstream_stream), media_type="text/event-stream")

    ollama_response = await ollama_client.chat(payload)
    return map_ollama_to_anthropic_response(body.model, ollama_response)
