"""Fire-and-forget background task helper.

For work that shouldn't block a response to the user (e.g. task summary
regeneration, embedding refresh) but must still run to completion with
its errors logged rather than silently disappearing. Safe in this app's
deployment model — a single long-running uvicorn process, not a
serverless function that might freeze after the response is sent.

Tasks are held in a module-level set per asyncio's own guidance: a task
with no other strong reference can be garbage-collected mid-execution.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_background_tasks: set[asyncio.Task] = set()


def fire_and_forget(coro: Coroutine[Any, Any, Any], *, name: str) -> asyncio.Task:
    task = asyncio.create_task(coro, name=name)
    _background_tasks.add(task)

    def _on_done(finished: asyncio.Task) -> None:
        _background_tasks.discard(finished)
        if finished.cancelled():
            return
        exc = finished.exception()
        if exc is not None:
            logger.error("background_task_failed", extra={"task_name": name}, exc_info=exc)

    task.add_done_callback(_on_done)
    return task


async def wait_for_background_tasks() -> None:
    """Waits for every currently tracked background task to finish.

    Not used in the request path — this exists for tests (assert on the
    effects of a backgrounded task deterministically) and for a clean
    shutdown hook if one is ever added.
    """
    pending = list(_background_tasks)
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
