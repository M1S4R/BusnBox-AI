from datetime import datetime

from pydantic import BaseModel, Field


class ChatAnalyticsSummaryResponse(BaseModel):
    total_responses: int = Field(
        default=0,
        ge=0,
    )

    average_response_time_ms: float | None = Field(
        default=None,
        ge=0.0,
    )

    p95_response_time_ms: float | None = Field(
        default=None,
        ge=0.0,
    )

    by_answer_source: dict[str, int] = Field(
        default_factory=dict,
    )

    by_intent: dict[str, int] = Field(
        default_factory=dict,
    )

    total_trips_returned: int = Field(
        default=0,
        ge=0,
    )

    total_recommendations_returned: int = Field(
        default=0,
        ge=0,
    )

    total_suggestions_returned: int = Field(
        default=0,
        ge=0,
    )

    grounded_responses: int = Field(
        default=0,
        ge=0,
    )

    last_updated_at: datetime | None = None
