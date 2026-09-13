import asyncio

from fastapi import APIRouter

from app.schemas.analytics import (
    ChatAnalyticsSummaryResponse,
)
from app.services.chat_analytics_service import (
    chat_analytics_service,
)

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)


@router.get(
    "/chat/summary",
    response_model=(
        ChatAnalyticsSummaryResponse
    ),
)
async def get_chat_analytics_summary(
) -> ChatAnalyticsSummaryResponse:
    summary = await asyncio.to_thread(
        chat_analytics_service.get_summary
    )

    return ChatAnalyticsSummaryResponse(
        total_responses=(
            summary.total_responses
        ),
        average_response_time_ms=(
            summary.average_response_time_ms
        ),
        p95_response_time_ms=(
            summary.p95_response_time_ms
        ),
        by_answer_source=(
            summary.by_answer_source
        ),
        by_intent=summary.by_intent,
        total_trips_returned=(
            summary.total_trips_returned
        ),
        total_recommendations_returned=(
            summary
            .total_recommendations_returned
        ),
        total_suggestions_returned=(
            summary
            .total_suggestions_returned
        ),
        grounded_responses=(
            summary.grounded_responses
        ),
        last_updated_at=(
            summary.last_updated_at
        ),
    )
