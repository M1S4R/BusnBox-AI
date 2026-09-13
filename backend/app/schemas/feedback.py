from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.chat import ChatIntent


class FeedbackRating(str, Enum):
    UP = "up"
    DOWN = "down"


class FeedbackReason(str, Enum):
    INACCURATE = "inaccurate"
    IRRELEVANT = "irrelevant"
    UNCLEAR = "unclear"
    INCOMPLETE = "incomplete"
    SLOW = "slow"
    OTHER = "other"


class FeedbackRequest(BaseModel):
    message_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description=(
            "Frontend identifier of the assistant "
            "message being rated."
        ),
    )

    conversation_id: str | None = Field(
        default=None,
        max_length=200,
        description="Associated conversation identifier.",
    )

    rating: FeedbackRating = Field(
        ...,
        description="Thumbs-up or thumbs-down rating.",
    )

    reason: FeedbackReason | None = Field(
        default=None,
        description=(
            "Optional reason for the submitted rating."
        ),
    )

    comment: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional written feedback.",
    )

    intent: ChatIntent | None = Field(
        default=None,
        description=(
            "Intent associated with the rated response."
        ),
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Optional non-sensitive frontend metadata."
        ),
    )


class FeedbackResponse(BaseModel):
    success: bool = True

    feedback_id: str

    message_id: str

    conversation_id: str | None = None

    rating: FeedbackRating

    reason: FeedbackReason | None = None

    comment: str | None = None

    intent: ChatIntent | None = None

    created_at: datetime

    updated_at: datetime


class FeedbackSummaryResponse(BaseModel):
    total: int = 0

    thumbs_up: int = 0

    thumbs_down: int = 0

    approval_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    reasons: dict[str, int] = Field(
        default_factory=dict
    )

    intents: dict[str, int] = Field(
        default_factory=dict
    )

    last_updated_at: datetime | None = None
