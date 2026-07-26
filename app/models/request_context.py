"""RequestContext: a transient object that exists only during processing.

Per 02_ARCHITECTURE.md §6 ("Request Context"), this is never persisted —
it is created when a message arrives and discarded once a response is
sent. It carries state between the Application Service, AI Orchestrator
and Decision Engine without those layers needing to pass a dozen
positional arguments to each other.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.schemas.ai import AIPipelineOutput


def _new_request_id() -> str:
    return f"REQ-{datetime.now(UTC):%Y%m%d}-{uuid.uuid4().hex[:8]}"


@dataclass
class RequestContext:
    user_id: str
    original_message: str
    request_id: str = field(default_factory=_new_request_id)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    ai_output: AIPipelineOutput | None = None
    started_at: float = field(default_factory=time.monotonic)

    @property
    def elapsed_seconds(self) -> float:
        return time.monotonic() - self.started_at
