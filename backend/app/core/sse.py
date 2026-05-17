"""SSE (Server-Sent Events) streaming utilities for FastAPI."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from starlette.responses import StreamingResponse


def sse_response(generator: AsyncGenerator[str, None]) -> StreamingResponse:
    """Wrap an async generator into an SSE StreamingResponse."""
    return StreamingResponse(
        _sse_wrapper(generator),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


async def _sse_wrapper(generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    """Format chunks as SSE data events."""
    try:
        async for chunk in generator:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        # Signal stream end
        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


def sse_event(event: str, data: Any) -> str:
    """Format a single named SSE event."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"
