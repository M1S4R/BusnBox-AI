import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from threading import Lock
from typing import Any

from app.schemas.chat import (
    ChatAnswerSource,
    ChatIntent,
)


@dataclass(frozen=True)
class ChatAnalyticsRecord:
    response_id: str
    conversation_id: str | None
    answer_source: ChatAnswerSource
    intent: ChatIntent
    response_time_ms: float
    trip_count: int
    recommendation_count: int
    suggestion_count: int
    source_count: int
    created_at: datetime


@dataclass(frozen=True)
class ChatAnalyticsSummary:
    total_responses: int
    average_response_time_ms: float | None
    p95_response_time_ms: float | None
    by_answer_source: dict[str, int]
    by_intent: dict[str, int]
    total_trips_returned: int
    total_recommendations_returned: int
    total_suggestions_returned: int
    grounded_responses: int
    last_updated_at: datetime | None


class ChatAnalyticsService:
    def __init__(
        self,
        data_path: Path | None = None,
    ) -> None:
        configured_path = os.getenv(
            "CHAT_ANALYTICS_DATA_PATH"
        )

        self._data_path = (
            data_path
            or (
                Path(configured_path)
                if configured_path
                else self._default_data_path()
            )
        )

        self._lock = Lock()

        self._records: dict[
            str,
            ChatAnalyticsRecord,
        ] = {}

        self._prepare_storage()
        self._load_existing_records()

    def record_response(
        self,
        response_id: str,
        conversation_id: str | None,
        answer_source: ChatAnswerSource,
        intent: ChatIntent,
        response_time_ms: float,
        trip_count: int,
        recommendation_count: int,
        suggestion_count: int,
        source_count: int,
    ) -> ChatAnalyticsRecord:
        normalized_response_id = (
            response_id.strip()
        )

        if not normalized_response_id:
            raise ValueError(
                "Response ID cannot be empty."
            )

        normalized_conversation_id = (
            conversation_id.strip()
            if conversation_id
            else None
        )

        record = ChatAnalyticsRecord(
            response_id=normalized_response_id,
            conversation_id=(
                normalized_conversation_id
            ),
            answer_source=answer_source,
            intent=intent,
            response_time_ms=round(
                max(response_time_ms, 0.0),
                2,
            ),
            trip_count=max(trip_count, 0),
            recommendation_count=max(
                recommendation_count,
                0,
            ),
            suggestion_count=max(
                suggestion_count,
                0,
            ),
            source_count=max(source_count, 0),
            created_at=datetime.now(
                timezone.utc
            ),
        )

        with self._lock:
            self._records[
                normalized_response_id
            ] = record

            self._append_record(record)

        return record

    def get_summary(
        self,
    ) -> ChatAnalyticsSummary:
        with self._lock:
            records = list(
                self._records.values()
            )

        if not records:
            return ChatAnalyticsSummary(
                total_responses=0,
                average_response_time_ms=None,
                p95_response_time_ms=None,
                by_answer_source={},
                by_intent={},
                total_trips_returned=0,
                total_recommendations_returned=0,
                total_suggestions_returned=0,
                grounded_responses=0,
                last_updated_at=None,
            )

        response_times = [
            record.response_time_ms
            for record in records
        ]

        by_answer_source: dict[str, int] = {}
        by_intent: dict[str, int] = {}

        for record in records:
            source_key = (
                record.answer_source.value
            )

            by_answer_source[source_key] = (
                by_answer_source.get(
                    source_key,
                    0,
                )
                + 1
            )

            intent_key = record.intent.value

            by_intent[intent_key] = (
                by_intent.get(
                    intent_key,
                    0,
                )
                + 1
            )

        grounded_responses = sum(
            1
            for record in records
            if record.source_count > 0
        )

        return ChatAnalyticsSummary(
            total_responses=len(records),
            average_response_time_ms=round(
                fmean(response_times),
                2,
            ),
            p95_response_time_ms=(
                self._calculate_percentile(
                    response_times,
                    percentile=0.95,
                )
            ),
            by_answer_source=(
                by_answer_source
            ),
            by_intent=by_intent,
            total_trips_returned=sum(
                record.trip_count
                for record in records
            ),
            total_recommendations_returned=sum(
                record.recommendation_count
                for record in records
            ),
            total_suggestions_returned=sum(
                record.suggestion_count
                for record in records
            ),
            grounded_responses=(
                grounded_responses
            ),
            last_updated_at=max(
                record.created_at
                for record in records
            ),
        )

    def _calculate_percentile(
        self,
        values: list[float],
        percentile: float,
    ) -> float | None:
        if not values:
            return None

        sorted_values = sorted(values)

        index = max(
            math.ceil(
                percentile
                * len(sorted_values)
            )
            - 1,
            0,
        )

        return round(
            sorted_values[index],
            2,
        )

    def _prepare_storage(self) -> None:
        self._data_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._data_path.touch(
            exist_ok=True
        )

    def _append_record(
        self,
        record: ChatAnalyticsRecord,
    ) -> None:
        payload = self._serialize_record(
            record
        )

        with self._data_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                )
            )

            file.write("\n")

    def _load_existing_records(
        self,
    ) -> None:
        with self._data_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                stripped = line.strip()

                if not stripped:
                    continue

                try:
                    payload = json.loads(
                        stripped
                    )

                    record = (
                        self._deserialize_record(
                            payload
                        )
                    )

                except (
                    ValueError,
                    TypeError,
                    KeyError,
                    json.JSONDecodeError,
                ):
                    continue

                self._records[
                    record.response_id
                ] = record

    def _serialize_record(
        self,
        record: ChatAnalyticsRecord,
    ) -> dict[str, Any]:
        return {
            "response_id": (
                record.response_id
            ),
            "conversation_id": (
                record.conversation_id
            ),
            "answer_source": (
                record.answer_source.value
            ),
            "intent": record.intent.value,
            "response_time_ms": (
                record.response_time_ms
            ),
            "trip_count": record.trip_count,
            "recommendation_count": (
                record.recommendation_count
            ),
            "suggestion_count": (
                record.suggestion_count
            ),
            "source_count": (
                record.source_count
            ),
            "created_at": (
                record.created_at.isoformat()
            ),
        }

    def _deserialize_record(
        self,
        payload: dict[str, Any],
    ) -> ChatAnalyticsRecord:
        return ChatAnalyticsRecord(
            response_id=str(
                payload["response_id"]
            ),
            conversation_id=(
                str(payload["conversation_id"])
                if payload.get(
                    "conversation_id"
                )
                else None
            ),
            answer_source=ChatAnswerSource(
                payload["answer_source"]
            ),
            intent=ChatIntent(
                payload["intent"]
            ),
            response_time_ms=float(
                payload["response_time_ms"]
            ),
            trip_count=int(
                payload.get("trip_count", 0)
            ),
            recommendation_count=int(
                payload.get(
                    "recommendation_count",
                    0,
                )
            ),
            suggestion_count=int(
                payload.get(
                    "suggestion_count",
                    0,
                )
            ),
            source_count=int(
                payload.get("source_count", 0)
            ),
            created_at=datetime.fromisoformat(
                payload["created_at"]
            ),
        )

    def _default_data_path(
        self,
    ) -> Path:
        return (
            Path(__file__).resolve().parents[1]
            / "data"
            / "chat_analytics.jsonl"
        )


chat_analytics_service = (
    ChatAnalyticsService()
)
