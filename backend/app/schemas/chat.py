from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatIntent(str, Enum):
    SEARCH_BUS = "search_bus"
    GREETING = "greeting"
    UPDATE_SEARCH = "update_search"
    CLEAR_SEARCH = "clear_search"
    REMOVE_FILTER = "remove_filter"
    HELP = "help"
    FAQ = "faq"
    UNKNOWN = "unknown"
    NONE = "none"


class ChatAnswerSource(str, Enum):
    FAQ = "faq"
    RAG = "rag"
    AI = "ai"
    INVENTORY = "inventory"


class ChatParameters(BaseModel):
    source: str | None = Field(
        default=None,
        description="Bus journey starting location.",
    )

    destination: str | None = Field(
        default=None,
        description="Bus journey destination.",
    )

    travel_date: str | None = Field(
        default=None,
        description=(
            "Travel date as today, tomorrow, "
            "next weekday, or YYYY-MM-DD."
        ),
    )

    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional bus-search filters.",
    )


class ChatSuggestion(BaseModel):
    id: str = Field(
        ...,
        description="Unique suggestion identifier.",
    )

    label: str = Field(
        ...,
        description="Suggestion chip text.",
    )

    message: str = Field(
        ...,
        description=(
            "Message sent when the suggestion "
            "is selected."
        ),
    )

    action: str = Field(
        ...,
        description="Frontend action type.",
    )


class KnowledgeSource(BaseModel):
    id: str = Field(
        ...,
        description=(
            "FAQ or knowledge document identifier."
        ),
    )

    title: str = Field(
        ...,
        description="Human-readable source title.",
    )

    kind: Literal[
        "faq",
        "knowledge_base",
    ] = Field(
        ...,
        description="Grounding source type.",
    )


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Message sent by the user.",
        examples=[
            (
                "Find buses from Chennai "
                "to Bangalore tomorrow"
            )
        ],
    )

    tenant_key: str = Field(
        default="busnbox",
        min_length=1,
        max_length=100,
        description="Tenant or company identifier.",
    )

    conversation_id: str | None = Field(
        default=None,
        max_length=200,
        description=(
            "Identifier used to maintain "
            "conversation context."
        ),
    )


class ChatResponse(BaseModel):
    success: bool = Field(
        default=True,
        description="Whether the request succeeded.",
    )

    response_id: str = Field(
        ...,
        description=(
            "Unique backend identifier for "
            "the assistant response."
        ),
    )

    answer_source: ChatAnswerSource = Field(
        ...,
        description=(
            "Backend path that generated "
            "the response."
        ),
    )

    response_time_ms: float = Field(
        ...,
        ge=0.0,
        description=(
            "Total backend response time "
            "in milliseconds."
        ),
    )

    reply: str = Field(
        ...,
        description="Assistant reply text.",
    )

    intent: ChatIntent = Field(
        ...,
        description="Detected user intent.",
    )

    parameters: ChatParameters = Field(
        default_factory=ChatParameters,
        description="Extracted search parameters.",
    )

    trips: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Validated inventory results.",
    )

    recommendations: list[
        dict[str, Any]
    ] = Field(
        default_factory=list,
        description=(
            "Recommendations generated from "
            "validated trip data."
        ),
    )

    suggestions: list[ChatSuggestion] = Field(
        default_factory=list,
        description="Contextual suggestion chips.",
    )

    sources: list[KnowledgeSource] = Field(
        default_factory=list,
        description=(
            "Sources used to ground the response."
        ),
    )

    grounding_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "FAQ or RAG retrieval confidence."
        ),
    )

    conversation_id: str | None = Field(
        default=None,
        description="Conversation identifier.",
    )


class ErrorDetail(BaseModel):
    code: str = Field(
        ...,
        description="Machine-readable error code.",
        examples=["INVENTORY_UNAVAILABLE"],
    )
    message: str = Field(
        ...,
        description="Human-readable error description.",
        examples=["Bus availability is temporarily unavailable."],
    )


class ChatErrorResponse(BaseModel):
    success: bool = Field(
        default=False,
        description="Whether the request succeeded (always false for errors).",
    )
    error: ErrorDetail = Field(
        ...,
        description="Standardized error details.",
    )
    detail: str | None = Field(
        default=None,
        description="Backwards compatible error detail string.",
    )