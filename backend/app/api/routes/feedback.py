import asyncio

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.schemas.feedback import (
    FeedbackRequest,
    FeedbackResponse,
    FeedbackSummaryResponse,
)
from app.services.feedback_service import (
    feedback_service,
)

router = APIRouter(
    prefix="/api/feedback",
    tags=["Feedback"],
)


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    request: FeedbackRequest,
) -> FeedbackResponse:
    try:
        record = await asyncio.to_thread(
            feedback_service.submit_feedback,
            request.message_id,
            request.conversation_id,
            request.rating,
            request.reason,
            request.comment,
            request.intent,
            request.metadata,
        )

        return FeedbackResponse(
            success=True,
            feedback_id=record.feedback_id,
            message_id=record.message_id,
            conversation_id=(
                record.conversation_id
            ),
            rating=record.rating,
            reason=record.reason,
            comment=record.comment,
            intent=record.intent,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        ) from exc


@router.get(
    "/summary",
    response_model=FeedbackSummaryResponse,
)
async def get_feedback_summary(
) -> FeedbackSummaryResponse:
    summary = await asyncio.to_thread(
        feedback_service.get_summary
    )

    return FeedbackSummaryResponse(
        total=summary.total,
        thumbs_up=summary.thumbs_up,
        thumbs_down=summary.thumbs_down,
        approval_rate=summary.approval_rate,
        reasons=summary.reasons,
        intents=summary.intents,
        last_updated_at=(
            summary.last_updated_at
        ),
    )
