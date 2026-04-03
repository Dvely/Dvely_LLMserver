import time
import uuid
from typing import Any

from app.schemas.anthropic import AnthropicMessageResponse, AnthropicTextContent, AnthropicUsage
from app.schemas.openai import (
    OpenAIChatCompletionResponse,
    OpenAIChoice,
    OpenAIChoiceMessage,
    OpenAIUsage,
)


def _map_finish_reason(done_reason: str | None) -> str:
    if not done_reason:
        return "stop"
    if done_reason in {"stop", "length"}:
        return done_reason
    return "stop"


def map_ollama_to_openai_response(public_model: str, ollama_response: dict[str, Any]) -> OpenAIChatCompletionResponse:
    prompt_tokens = int(ollama_response.get("prompt_eval_count") or 0)
    completion_tokens = int(ollama_response.get("eval_count") or 0)

    return OpenAIChatCompletionResponse(
        id=f"chatcmpl_{uuid.uuid4().hex}",
        created=int(time.time()),
        model=public_model,
        choices=[
            OpenAIChoice(
                index=0,
                message=OpenAIChoiceMessage(
                    role="assistant",
                    content=(ollama_response.get("message") or {}).get("content", ""),
                ),
                finish_reason=_map_finish_reason(ollama_response.get("done_reason")),
            )
        ],
        usage=OpenAIUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


def map_ollama_to_anthropic_response(public_model: str, ollama_response: dict[str, Any]) -> AnthropicMessageResponse:
    return AnthropicMessageResponse(
        id=f"msg_{uuid.uuid4().hex}",
        model=public_model,
        content=[AnthropicTextContent(text=(ollama_response.get("message") or {}).get("content", ""))],
        stop_reason="end_turn",
        usage=AnthropicUsage(
            input_tokens=int(ollama_response.get("prompt_eval_count") or 0),
            output_tokens=int(ollama_response.get("eval_count") or 0),
        ),
    )
