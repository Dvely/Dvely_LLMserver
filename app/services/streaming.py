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


def map_anthropic_stream(
    public_model: str,
    upstream_stream: AsyncIterator[dict[str, Any]],
) -> AsyncIterator[dict[str, str]]:
    async def _generator() -> AsyncIterator[dict[str, str]]:
        message_id = f"msg_{uuid.uuid4().hex}"

        yield {
            "event": "message_start",
            "data": json.dumps(
                {
                    "type": "message_start",
                    "message": {
                        "id": message_id,
                        "type": "message",
                        "role": "assistant",
                        "model": public_model,
                        "content": [],
                    },
                },
                ensure_ascii=False,
            ),
        }

        yield {
            "event": "content_block_start",
            "data": json.dumps(
                {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {"type": "text", "text": ""},
                },
                ensure_ascii=False,
            ),
        }

        async for chunk in upstream_stream:
            piece = ((chunk.get("message") or {}).get("content")) or ""
            done = bool(chunk.get("done"))

            if piece:
                yield {
                    "event": "content_block_delta",
                    "data": json.dumps(
                        {
                            "type": "content_block_delta",
                            "index": 0,
                            "delta": {"type": "text_delta", "text": piece},
                        },
                        ensure_ascii=False,
                    ),
                }

            if done:
                yield {
                    "event": "content_block_stop",
                    "data": json.dumps({"type": "content_block_stop", "index": 0}, ensure_ascii=False),
                }
                yield {
                    "event": "message_delta",
                    "data": json.dumps(
                        {
                            "type": "message_delta",
                            "delta": {"stop_reason": "end_turn"},
                            "usage": {
                                "input_tokens": int(chunk.get("prompt_eval_count") or 0),
                                "output_tokens": int(chunk.get("eval_count") or 0),
                            },
                        },
                        ensure_ascii=False,
                    ),
                }
                yield {
                    "event": "message_stop",
                    "data": json.dumps({"type": "message_stop"}, ensure_ascii=False),
                }

    return _generator()
