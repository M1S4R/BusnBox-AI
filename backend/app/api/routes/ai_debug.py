from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.intent_extractor import (
    IntentExtractionError,
    IntentExtractor,
)
from app.schemas.ai_intent import IntentExtractionResult

router = APIRouter(
    prefix="/api/debug/ai",
    tags=["AI Debug"],
)


class IntentDebugRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


@router.post(
    "/intent",
    response_model=IntentExtractionResult,
)
async def extract_intent(
    payload: IntentDebugRequest,
) -> IntentExtractionResult:
    extractor = IntentExtractor()

    try:
        return await extractor.extract(payload.message)

    except IntentExtractionError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc