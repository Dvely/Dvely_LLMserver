from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class AnthropicTextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class AnthropicMessageInput(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[str, list[AnthropicTextContent]]


class AnthropicMessageRequest(BaseModel):
    model: str = Field(min_length=1)
    messages: list[AnthropicMessageInput] = Field(min_length=1)
    max_tokens: Optional[int] = None
    system: Optional[str] = None
    stream: bool = False


class AnthropicUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class AnthropicMessageResponse(BaseModel):
    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    model: str
    content: list[AnthropicTextContent]
    stop_reason: str = "end_turn"
    usage: AnthropicUsage
