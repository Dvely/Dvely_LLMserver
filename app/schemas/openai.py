from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class OpenAIChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"] = Field(
        description="Message role",
        examples=["user"],
    )
    content: str = Field(
        min_length=1,
        description="Message content",
        examples=["파이썬으로 두 수의 합을 반환하는 함수만 작성해줘."],
    )


class OpenAIChatCompletionRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "model": "qwen2.5-coder:3b",
                    "messages": [
                        {
                            "role": "user",
                            "content": "파이썬으로 두 수의 합을 반환하는 함수만 작성해줘.",
                        }
                    ],
                    "stream": False,
                }
            ]
        }
    )

    model: str = Field(min_length=1, description="Public model alias")
    messages: list[OpenAIChatMessage] = Field(min_length=1, description="Conversation messages")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature (optional)")
    top_p: Optional[float] = Field(default=None, description="Nucleus sampling probability (optional)")
    max_tokens: Optional[int] = Field(default=None, description="Maximum generated tokens (optional)")
    stream: bool = Field(default=False, description="If true, returns SSE stream chunks")


class OpenAIChoiceMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class OpenAIChoice(BaseModel):
    index: int = 0
    message: OpenAIChoiceMessage
    finish_reason: str


class OpenAIUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class OpenAIChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[OpenAIChoice]
    usage: OpenAIUsage


class OpenAIStreamDelta(BaseModel):
    role: Optional[Literal["assistant"]] = None
    content: Optional[str] = None


class OpenAIStreamChoice(BaseModel):
    index: int = 0
    delta: OpenAIStreamDelta
    finish_reason: Optional[str] = None


class OpenAIStreamChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[OpenAIStreamChoice]


class OpenAIExtraPayload(BaseModel):
    """Holds ignored fields without rejecting the request."""

    data: dict[str, Any] = Field(default_factory=dict)
