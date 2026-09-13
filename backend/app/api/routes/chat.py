import asyncio
import logging
import re
import secrets
from dataclasses import asdict, is_dataclass
from datetime import date
from time import perf_counter
from typing import Any
from uuid import uuid4

import httpx
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.chat import (
    ChatAnswerSource,
    ChatErrorResponse,
    ChatIntent,
    ChatParameters,
    ChatRequest,
    ChatResponse,
    ChatSuggestion,
    KnowledgeSource,
)
from app.schemas.inventory import (
    InventorySearchRequest,
)
from app.services.ai_service import (
    AIService,
    AIServiceError,
)
from app.services.chat_analytics_service import (
    chat_analytics_service,
)
from app.services.chat_response_service import (
    chat_response_service,
)
from app.services.conversation_service import (
    conversation_service,
)
from app.services.date_service import (
    extract_date_reference,
    resolve_calendar_date,
)
from app.services.faq_service import (
    faq_service,
)
from app.services.inventory_service import (
    InventoryService,
    InventoryServiceError,
)
from app.services.query_refinement_service import (
    query_refinement_service,
)
from app.services.rag_service import (
    RAGAnswer,
    RAGServiceError,
    rag_service,
)
from app.services.recommendation_service import (
    recommendation_service,
)
from app.services.route_service import (
    route_service,
)
from app.services.suggestion_service import (
    suggestion_service,
)

router = APIRouter(
    tags=["Chat"],
)

ai_service = AIService()
inventory_service = InventoryService()
logger = logging.getLogger(__name__)


def resolve_travel_date(
    value: str | None,
    *,
    reference_date: date | None = None,
) -> date | None:
    """Resolve natural-language and explicit travel dates.

    reference_date is injectable for deterministic tests.
    Production uses the current UTC date.
    """
    if value is None or not value.strip():
        return None

    resolved = resolve_calendar_date(
        value,
        reference_date=reference_date,
    )
    if resolved is not None:
        return resolved

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Travel date must be today, tomorrow, "
            "day after tomorrow, in N days, this/next "
            "weekday or weekend, DD/MM/YYYY, DD-MM-YYYY, "
            "YYYY-MM-DD, or a month/day format."
        ),
    )


def extract_travel_date_reference(
    message: str,
) -> str | None:
    """Extract a user-supplied travel date deterministically."""
    return extract_date_reference(message)


def message_contains_travel_date(
    message: str,
) -> bool:
    """Return True only when the user supplied a date."""

    return (
        extract_travel_date_reference(message)
        is not None
    )


def sanitize_ai_travel_date(
    *,
    message: str,
    parameters: ChatParameters,
) -> ChatParameters:
    """Prevent Gemini from inventing a travel date."""

    if message_contains_travel_date(message):
        return parameters

    return parameters.model_copy(
        update={
            "travel_date": None,
        }
    )


def apply_deterministic_travel_date(
    *,
    message: str,
    parameters: ChatParameters,
) -> ChatParameters:
    """Override Gemini travel_date with the user's date."""

    detected_date = extract_travel_date_reference(
        message
    )

    if detected_date is None:
        return parameters

    return parameters.model_copy(
        update={
            "travel_date": detected_date,
        }
    )


def empty_parameters() -> ChatParameters:
    return ChatParameters(
        source=None,
        destination=None,
        travel_date=None,
        filters={},
    )


def get_current_parameters(
    conversation_id: str | None,
) -> ChatParameters:
    if not conversation_id:
        return empty_parameters()

    context = conversation_service.get_context(
        conversation_id
    )

    return context.parameters


def should_start_new_search(
    current: ChatParameters,
    incoming: ChatParameters,
) -> bool:
    if (
        not incoming.source
        or not incoming.destination
    ):
        return False

    if (
        not current.source
        or not current.destination
    ):
        return False

    source_changed = (
        current.source.casefold()
        != incoming.source.casefold()
    )

    destination_changed = (
        current.destination.casefold()
        != incoming.destination.casefold()
    )

    return (
        source_changed
        or destination_changed
    )


def has_search_context(
    parameters: ChatParameters,
) -> bool:
    return bool(
        parameters.source
        or parameters.destination
        or parameters.travel_date
        or parameters.filters
    )


def message_looks_like_travel_search(
    message: str,
) -> bool:
    """Detect obvious travel/search requests independently of Gemini."""

    normalized = " ".join(
        message.strip().lower().split()
    )

    if not normalized:
        return False

    travel_search_phrases = (
        "find buses",
        "find a bus",
        "search buses",
        "search a bus",
        "show buses",
        "show bus",
        "available buses",
        "available bus",
        "bus from",
        "buses from",
        "travel from",
        "trip from",
        "trips from",
        "journey from",
        "route from",
        "routes from",
        "go from",
        "going from",
        "get me a bus",
        "book a bus from",
    )

    if any(
        phrase in normalized
        for phrase in travel_search_phrases
    ):
        return True

    return bool(
        re.search(
            r"\b[a-z]+\s+to\s+[a-z]+\b",
            normalized,
        )
    )


def serialize_recommendation(
    recommendation: Any,
) -> dict[str, Any]:
    if isinstance(recommendation, dict):
        return recommendation

    if is_dataclass(recommendation):
        return asdict(recommendation)

    model_dump = getattr(
        recommendation,
        "model_dump",
        None,
    )

    if callable(model_dump):
        try:
            result = model_dump(mode="json")
        except TypeError:
            result = model_dump()

        if isinstance(result, dict):
            return result

    recommendation_data = getattr(
        recommendation,
        "__dict__",
        None,
    )

    if isinstance(
        recommendation_data,
        dict,
    ):
        return dict(
            recommendation_data
        )

    raise TypeError(
        "Unsupported recommendation type: "
        f"{type(recommendation).__name__}"
    )


def serialize_suggestion(
    suggestion: Any,
) -> ChatSuggestion:
    if isinstance(
        suggestion,
        ChatSuggestion,
    ):
        return suggestion

    if isinstance(suggestion, dict):
        return ChatSuggestion.model_validate(
            suggestion
        )

    if is_dataclass(suggestion):
        return ChatSuggestion.model_validate(
            asdict(suggestion)
        )

    model_dump = getattr(
        suggestion,
        "model_dump",
        None,
    )

    if callable(model_dump):
        try:
            result = model_dump(mode="json")
        except TypeError:
            result = model_dump()

        return ChatSuggestion.model_validate(
            result
        )

    suggestion_data = getattr(
        suggestion,
        "__dict__",
        None,
    )

    if isinstance(
        suggestion_data,
        dict,
    ):
        return ChatSuggestion.model_validate(
            suggestion_data
        )

    raise TypeError(
        "Unsupported suggestion type: "
        f"{type(suggestion).__name__}"
    )


def build_rag_sources(
    rag_answer: RAGAnswer,
) -> list[KnowledgeSource]:
    return [
        KnowledgeSource(
            id=source_id,
            title=source_title,
            kind="knowledge_base",
        )
        for source_id, source_title in zip(
            rag_answer.source_ids,
            rag_answer.source_titles,
        )
    ]


async def build_tracked_response(
    *,
    started_at: float,
    conversation_id: str | None,
    reply: str,
    intent: ChatIntent,
    answer_source: ChatAnswerSource,
    parameters: ChatParameters,
    trips: list[dict[str, Any]] | None = None,
    recommendations: (
        list[dict[str, Any]] | None
    ) = None,
    suggestions: (
        list[ChatSuggestion] | None
    ) = None,
    sources: (
        list[KnowledgeSource] | None
    ) = None,
    grounding_confidence: (
        float | None
    ) = None,
) -> ChatResponse:
    final_trips = trips or []

    final_recommendations = (
        recommendations or []
    )

    final_suggestions = (
        suggestions or []
    )

    final_sources = sources or []

    response_id = str(uuid4())

    response_time_ms = round(
        (
            perf_counter()
            - started_at
        )
        * 1000,
        2,
    )

    await asyncio.to_thread(
        chat_analytics_service.record_response,
        response_id,
        conversation_id,
        answer_source,
        intent,
        response_time_ms,
        len(final_trips),
        len(final_recommendations),
        len(final_suggestions),
        len(final_sources),
    )

    return ChatResponse(
        success=True,
        response_id=response_id,
        answer_source=answer_source,
        response_time_ms=response_time_ms,
        reply=reply,
        intent=intent,
        parameters=parameters,
        trips=final_trips,
        recommendations=(
            final_recommendations
        ),
        suggestions=final_suggestions,
        sources=final_sources,
        grounding_confidence=(
            grounding_confidence
        ),
        conversation_id=conversation_id,
    )


def build_inventory_search_request(
    source: str,
    destination: str,
    travel_date: date,
    filters: dict[str, Any],
) -> InventorySearchRequest:
    search_data: dict[str, Any] = {
        "source": source,
        "destination": destination,
        "travel_date": travel_date,
        "page": 1,
        "page_size": 50,
    }

    optional_filters = {
        "operator": filters.get("operator"),
        "bus_type": filters.get("bus_type"),
        "maximum_price": filters.get(
            "maximum_price"
        ),
        "minimum_seats": filters.get(
            "minimum_seats"
        ),
        "departure_time": filters.get(
            "departure_time"
        ),
    }

    for key, value in (
        optional_filters.items()
    ):
        if value is not None:
            search_data[key] = value

    return InventorySearchRequest(
        **search_data
    )


def build_missing_parameter_payload(
    parameters: ChatParameters,
) -> tuple[
    str,
    list[ChatSuggestion],
] | None:
    if not parameters.source and not parameters.destination:
        suggestion_results = (
            suggestion_service
            .build_missing_parameter_suggestions(
                missing_parameter="source"
            )
        )

        suggestions = [
            serialize_suggestion(
                suggestion
            )
            for suggestion in (
                suggestion_results
            )
        ]

        reply = (
            chat_response_service
            .build_missing_route_reply()
        )

        return reply, suggestions

    if not parameters.source:
        suggestion_results = (
            suggestion_service
            .build_missing_parameter_suggestions(
                missing_parameter="source"
            )
        )

        suggestions = [
            serialize_suggestion(
                suggestion
            )
            for suggestion in (
                suggestion_results
            )
        ]

        reply = (
            chat_response_service
            .build_missing_source_reply()
        )

        return reply, suggestions

    if not parameters.destination:
        suggestion_results = (
            suggestion_service
            .build_missing_parameter_suggestions(
                missing_parameter=(
                    "destination"
                )
            )
        )

        suggestions = [
            serialize_suggestion(
                suggestion
            )
            for suggestion in (
                suggestion_results
            )
        ]

        reply = (
            chat_response_service
            .build_missing_destination_reply(
                parameters.source
            )
        )

        return reply, suggestions

    if not parameters.travel_date:
        suggestion_results = (
            suggestion_service
            .build_missing_parameter_suggestions(
                missing_parameter=(
                    "travel_date"
                )
            )
        )

        suggestions = [
            serialize_suggestion(
                suggestion
            )
            for suggestion in (
                suggestion_results
            )
        ]

        reply = (
            chat_response_service
            .build_missing_date_reply(
                parameters.source,
                parameters.destination,
            )
        )

        return reply, suggestions

    return None


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ChatErrorResponse,
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ChatErrorResponse,
        },
        status.HTTP_408_REQUEST_TIMEOUT: {
            "model": ChatErrorResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ChatErrorResponse,
        },
    },
    summary="Chat with BusNBox AI (legacy endpoint)",
)
@router.post(
    "/api/v1/chat",
    response_model=ChatResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ChatErrorResponse,
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ChatErrorResponse,
        },
        status.HTTP_408_REQUEST_TIMEOUT: {
            "model": ChatErrorResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ChatErrorResponse,
        },
    },
    summary="Chat with BusNBox AI (v1 public endpoint)",
)
async def chat(
    request: ChatRequest,
    http_request: Request,
) -> ChatResponse:
    started_at = perf_counter()
    message = request.message.strip()

    # Optional service-to-service authentication
    if settings.busnbox_api_key:
        api_key_header = http_request.headers.get(settings.busnbox_api_key_header)
        auth_header = http_request.headers.get("Authorization")
        bearer_key = (
            auth_header.replace("Bearer ", "").strip()
            if auth_header and auth_header.startswith("Bearer ")
            else None
        )
        supplied_key = api_key_header or bearer_key
        if not supplied_key or not secrets.compare_digest(
            supplied_key,
            settings.busnbox_api_key,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing service API key.",
            )

    conversation_id = (
        request.conversation_id
        or str(uuid4())
    )

    logger.info(
        "conversation_id=%s message=%s",
        conversation_id,
        message,
    )

    if not message:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail="Message cannot be empty.",
        )

    try:
        # ---------------------------------------------------------
        # 1. Deterministic FAQ handling
        # ---------------------------------------------------------
        faq_match = (
            faq_service.find_answer(
                message
            )
        )

        if faq_match is not None:
            current_parameters = (
                get_current_parameters(
                    conversation_id
                )
            )

            faq_source = KnowledgeSource(
                id=faq_match.faq_id,
                title=faq_match.question,
                kind="faq",
            )

            return await build_tracked_response(
                started_at=started_at,
                conversation_id=(
                    conversation_id
                ),
                reply=faq_match.answer,
                intent=ChatIntent.FAQ,
                answer_source=(
                    ChatAnswerSource.FAQ
                ),
                parameters=current_parameters,
                sources=[faq_source],
                grounding_confidence=(
                    faq_match.confidence
                ),
            )

        # ---------------------------------------------------------
        # 2. Existing conversation context
        # ---------------------------------------------------------
        current_parameters = (
            get_current_parameters(
                conversation_id
            )
        )

        # ---------------------------------------------------------
        # 3. Gemini analysis
        # ---------------------------------------------------------
        analysis = (
            await ai_service.analyze_message(
                message=message,
                current_parameters=(
                    current_parameters
                ),
            )
        )

        logger.info(
            "conversation_id=%s "
            "Gemini intent=%s parameters=%s",
            conversation_id,
            analysis.intent,
            analysis.parameters,
        )

        # ---------------------------------------------------------
        # 3b. Check explicit clear search intent / phrases
        # ---------------------------------------------------------
        clear_search_phrases = (
            "new search",
            "clear search",
            "start over",
            "reset search",
            "begin again",
            "clear everything",
        )
        normalized_msg = " ".join(message.strip().lower().split())
        if analysis.intent == ChatIntent.CLEAR_SEARCH or normalized_msg in clear_search_phrases:
            conversation_service.clear_context(conversation_id)
            return await build_tracked_response(
                started_at=started_at,
                conversation_id=conversation_id,
                reply="Sure — where would you like to travel?",
                intent=ChatIntent.CLEAR_SEARCH,
                answer_source=ChatAnswerSource.AI,
                parameters=empty_parameters(),
                suggestions=[
                    ChatSuggestion(id="s-welcome-1", label="Chennai to Bangalore tomorrow", message="Chennai to Bangalore tomorrow", action="search"),
                    ChatSuggestion(id="s-welcome-2", label="Mumbai to Pune today", message="Mumbai to Pune today", action="search"),
                    ChatSuggestion(id="s-welcome-3", label="Delhi to Jaipur this weekend", message="Delhi to Jaipur this weekend", action="search"),
                ],
            )

        # ---------------------------------------------------------
        # 4. Deterministic travel-date validation
        # ---------------------------------------------------------
        sanitized_parameters = (
            sanitize_ai_travel_date(
                message=message,
                parameters=analysis.parameters,
            )
        )

        sanitized_parameters = (
            apply_deterministic_travel_date(
                message=message,
                parameters=sanitized_parameters,
            )
        )

        detected_travel_date = (
            extract_travel_date_reference(
                message
            )
        )

        if detected_travel_date is not None:
            logger.info(
                "conversation_id=%s "
                "Deterministic travel date detected: %s",
                conversation_id,
                detected_travel_date,
            )

        # ---------------------------------------------------------
        # 4b. Deterministic route extraction & typo tolerance
        # ---------------------------------------------------------
        extracted_route = route_service.extract_route(
            message=message,
            current_source=current_parameters.source,
            current_destination=current_parameters.destination,
        )

        incoming_source = extracted_route.source or sanitized_parameters.source
        incoming_destination = extracted_route.destination or sanitized_parameters.destination

        incoming_source = route_service.normalize_city(incoming_source) or incoming_source
        incoming_destination = route_service.normalize_city(incoming_destination) or incoming_destination

        sanitized_parameters = sanitized_parameters.model_copy(
            update={
                "source": incoming_source,
                "destination": incoming_destination,
            }
        )

        if (
            sanitized_parameters
            != analysis.parameters
        ):
            analysis = analysis.model_copy(
                update={
                    "parameters": (
                        sanitized_parameters
                    ),
                }
            )

            logger.info(
                "conversation_id=%s "
                "Applied deterministic travel-date and route "
                "validation: %s",
                conversation_id,
                sanitized_parameters,
            )

        # ---------------------------------------------------------
        # 5. Detect source/destination changes
        # ---------------------------------------------------------
        is_partial_route_update = (
            extracted_route.is_correction
            or (extracted_route.source is None and extracted_route.destination is not None)
            or (extracted_route.source is not None and extracted_route.destination is None)
        )

        if not is_partial_route_update and should_start_new_search(
            current=current_parameters,
            incoming=sanitized_parameters,
        ):
            conversation_service.clear_context(
                conversation_id
            )

            current_parameters = (
                empty_parameters()
            )

        # ---------------------------------------------------------
        # 6. Refine parameters
        # ---------------------------------------------------------
        refinement = (
            query_refinement_service.refine(
                message=message,
                current=current_parameters,
                incoming=sanitized_parameters,
            )
        )

        logger.info(
            "conversation_id=%s "
            "Refined parameters=%s",
            conversation_id,
            refinement.parameters,
        )

        # ---------------------------------------------------------
        # 7. Determine search intent
        # ---------------------------------------------------------
        is_search_request = (
            analysis.intent
            == ChatIntent.SEARCH_BUS
        )

        is_follow_up_search = (
            refinement.was_refinement
            and has_search_context(
                current_parameters
            )
        )

        has_extracted_endpoint = bool(
            extracted_route.source or extracted_route.destination
        )

        deterministic_search = (
            message_looks_like_travel_search(
                message
            )
            or detected_travel_date is not None
            or has_extracted_endpoint
        )

        has_new_route = bool(
            sanitized_parameters.source
            and sanitized_parameters.destination
        )

        if (
            analysis.intent
            in (ChatIntent.FAQ, ChatIntent.HELP)
            and not has_new_route
        ):
            should_search = False
        else:
            should_search = (
                is_search_request
                or is_follow_up_search
                or deterministic_search
            )

        logger.info(
            "conversation_id=%s "
            "is_search_request=%s "
            "is_follow_up_search=%s "
            "deterministic_search=%s "
            "should_search=%s",
            conversation_id,
            is_search_request,
            is_follow_up_search,
            deterministic_search,
            should_search,
        )

        # ---------------------------------------------------------
        # 8. RAG / normal AI response
        # ---------------------------------------------------------
        if not should_search:
            rag_answer = await rag_service.answer(
                message
            )

            if rag_answer is not None:
                return await build_tracked_response(
                    started_at=started_at,
                    conversation_id=(
                        conversation_id
                    ),
                    reply=rag_answer.answer,
                    intent=ChatIntent.FAQ,
                    answer_source=(
                        ChatAnswerSource.RAG
                    ),
                    parameters=current_parameters,
                    sources=build_rag_sources(
                        rag_answer
                    ),
                    grounding_confidence=(
                        rag_answer.confidence
                    ),
                )

            return await build_tracked_response(
                started_at=started_at,
                conversation_id=(
                    conversation_id
                ),
                reply=analysis.reply,
                intent=analysis.intent,
                answer_source=(
                    ChatAnswerSource.AI
                ),
                parameters=(
                    analysis.parameters
                ),
            )

        # ---------------------------------------------------------
        # 9. Update conversation context
        # ---------------------------------------------------------
        refined_parameters = (
            refinement.parameters
        )

        if detected_travel_date is not None:
            refined_parameters = (
                refined_parameters.model_copy(
                    update={
                        "travel_date": (
                            detected_travel_date
                        ),
                    }
                )
            )

        updated_context = (
            conversation_service
            .update_context(
                conversation_id=(
                    conversation_id
                ),
                new_parameters=(
                    refined_parameters
                ),
            )
        )

        merged_parameters = (
            updated_context.parameters
        )

        if refinement.removed_filters:
            clean_filters = dict(merged_parameters.filters)
            for rf in refinement.removed_filters:
                clean_filters.pop(rf, None)
            merged_parameters = merged_parameters.model_copy(
                update={"filters": clean_filters}
            )
            if conversation_id and conversation_id in conversation_service._conversations:
                conversation_service._conversations[conversation_id].parameters = (
                    conversation_service._conversations[conversation_id].parameters.model_copy(
                        update={"filters": clean_filters}
                    )
                )

        # ---------------------------------------------------------
        # Deterministic date must always win.
        #
        # The conversation service may merge/preserve parameters,
        # but it must never remove a date explicitly supplied by
        # the user in the current message.
        # ---------------------------------------------------------
        if detected_travel_date is not None:
            merged_parameters = (
                merged_parameters.model_copy(
                    update={
                        "travel_date": (
                            detected_travel_date
                        ),
                    }
                )
            )

            logger.info(
                "conversation_id=%s "
                "Forced deterministic travel date "
                "after context update: %s",
                conversation_id,
                detected_travel_date,
            )

        logger.info(
            "conversation_id=%s "
            "Merged parameters=%s",
            conversation_id,
            merged_parameters,
        )

        # ---------------------------------------------------------
        # 10. Missing parameters
        # ---------------------------------------------------------
        missing_payload = (
            build_missing_parameter_payload(
                merged_parameters
            )
        )

        if missing_payload is not None:
            (
                missing_reply,
                missing_suggestions,
            ) = missing_payload

            return await build_tracked_response(
                started_at=started_at,
                conversation_id=(
                    conversation_id
                ),
                reply=missing_reply,
                intent=ChatIntent.SEARCH_BUS,
                answer_source=(
                    ChatAnswerSource.INVENTORY
                ),
                parameters=merged_parameters,
                suggestions=(
                    missing_suggestions
                ),
            )

        # ---------------------------------------------------------
        # 11. Validate source + destination
        # ---------------------------------------------------------
        source = merged_parameters.source
        destination = (
            merged_parameters.destination
        )

        if (
            source is None
            or destination is None
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Source and destination "
                    "are required."
                ),
            )

        # ---------------------------------------------------------
        # 12. Resolve date
        # ---------------------------------------------------------
        resolved_date = (
            resolve_travel_date(
                merged_parameters.travel_date
            )
        )

        if resolved_date is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "A valid travel date "
                    "is required."
                ),
            )

        logger.info(
            "conversation_id=%s "
            "Resolved travel date: %s",
            conversation_id,
            resolved_date.isoformat(),
        )

        # ---------------------------------------------------------
        # 13. Build inventory request
        # ---------------------------------------------------------
        search_request = (
            build_inventory_search_request(
                source=source,
                destination=destination,
                travel_date=resolved_date,
                filters=(
                    merged_parameters.filters
                    or {}
                ),
            )
        )

        # ---------------------------------------------------------
        # 14. Search inventory
        # ---------------------------------------------------------
        search_result = (
            await inventory_service.search_trips(
                search_request
            )
        )

        trips = [
            trip.model_dump(mode="json")
            for trip in search_result.trips
        ]

        # ---------------------------------------------------------
        # 15. Apply deterministic sorting
        # ---------------------------------------------------------
        trips = (
            query_refinement_service
            .sort_trips(
                trips=trips,
                sort_by=refinement.sort_by,
                sort_order=(
                    refinement.sort_order
                ),
            )
        )

        # ---------------------------------------------------------
        # 16. Recommendations
        # ---------------------------------------------------------
        recommendation_results = (
            recommendation_service
            .build_recommendations(
                trips=trips
            )
        )

        recommendations = [
            serialize_recommendation(
                recommendation
            )
            for recommendation in (
                recommendation_results
            )
        ]

        # ---------------------------------------------------------
        # 17. Deterministic search reply
        # ---------------------------------------------------------
        reply = (
            chat_response_service
            .build_search_reply(
                parameters=merged_parameters,
                trips=trips,
                refinement=refinement,
                resolved_date=resolved_date,
            )
        )

        # ---------------------------------------------------------
        # 18. Suggestions
        # ---------------------------------------------------------
        suggestion_results = (
            suggestion_service
            .build_search_suggestions(
                parameters=merged_parameters,
                trips=trips,
            )
        )

        suggestions = [
            serialize_suggestion(
                suggestion
            )
            for suggestion in (
                suggestion_results
            )
        ]

        # ---------------------------------------------------------
        # 19. Final response
        # ---------------------------------------------------------
        return await build_tracked_response(
            started_at=started_at,
            conversation_id=(
                conversation_id
            ),
            reply=reply,
            intent=ChatIntent.SEARCH_BUS,
            answer_source=(
                ChatAnswerSource.INVENTORY
            ),
            parameters=merged_parameters,
            trips=trips,
            recommendations=recommendations,
            suggestions=suggestions,
        )

    except HTTPException:
        raise

    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Chat data validation failed: "
                f"{exc}"
            ),
        ) from exc

    except (
        AIServiceError,
        RAGServiceError,
        InventoryServiceError,
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(exc),
        ) from exc

    except (TimeoutError, httpx.TimeoutException) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_408_REQUEST_TIMEOUT
            ),
            detail="The request timed out while contacting upstream services.",
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unhandled chat error "
            "conversation_id=%s",
            conversation_id,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to complete the "
                "chat request. Please try again later."
            ),
        ) from exc