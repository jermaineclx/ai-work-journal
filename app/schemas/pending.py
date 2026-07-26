"""A Daily Log awaiting user confirmation via Telegram inline buttons.

Persisted (not just kept in memory) so a backend restart between a
message and the user's button tap doesn't silently lose the pending
action (16.2 Reliability — "Partial writes should be avoided").
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.schemas.ai import AIPipelineOutput
from app.schemas.decision import DecisionSchema


class PendingConfirmation(BaseModel):
    request_id: str
    user_id: str
    original_message: str
    ai_output: AIPipelineOutput
    decision: DecisionSchema
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
