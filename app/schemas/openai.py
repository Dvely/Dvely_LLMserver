from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class OpenAIChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class OpenAIChatCompletionRequest(BaseModel):
    model: str = Field(min_length=1)
    messages: list[OpenAIChatMessage] = Field(min_length=1)
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False


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
