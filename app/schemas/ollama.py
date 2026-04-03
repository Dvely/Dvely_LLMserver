from typing import Any, Literal, Optional

from pydantic import BaseModel


class OllamaMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class OllamaChatRequest(BaseModel):
    model: str
    messages: list[OllamaMessage]
    stream: bool = False
    options: Optional[dict[str, Any]] = None
    keep_alive: Optional[str] = None


class OllamaChatResponse(BaseModel):
    model: str
    message: OllamaMessage
    done: bool
    done_reason: Optional[str] = None
    prompt_eval_count: int = 0
    eval_count: int = 0
