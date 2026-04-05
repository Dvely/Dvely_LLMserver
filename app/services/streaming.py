import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any


def map_openai_stream(
    public_model: str,
    upstream_stream: AsyncIterator[dict[str, Any]],
) -> AsyncIterator[dict[str, str]]:
    async def _generator() -> AsyncIterator[dict[str, str]]:
        stream_id = f"chatcmpl_{uuid.uuid4().hex}"
        created = int(time.time())

        initial = {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": public_model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": None,
                }
            ],
        }
        yield {"data": json.dumps(initial, ensure_ascii=False)}

        async for chunk in upstream_stream:
            piece = ((chunk.get("message") or {}).get("content")) or ""
            done = bool(chunk.get("done"))
            done_reason = chunk.get("done_reason")

            payload = {
                "id": stream_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": public_model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": piece} if piece else {},
                        "finish_reason": "stop" if done else None,
                    }
                ],
            }
            if done and done_reason == "length":
                payload["choices"][0]["finish_reason"] = "length"

            yield {"data": json.dumps(payload, ensure_ascii=False)}

        yield {"data": "[DONE]"}

    return _generator()
