import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from app.schemas.chat import ChatIntent
from app.schemas.feedback import (
    FeedbackRating,
    FeedbackReason,
)


@dataclass(frozen=True)
class FeedbackRecord:
    feedback_id: str
    message_id: str
    conversation_id: str | None
    rating: FeedbackRating
    reason: FeedbackReason | None
    comment: str | None
    intent: ChatIntent | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FeedbackSummary:
    total: int
    thumbs_up: int
    thumbs_down: int
    approval_rate: float | None
    reasons: dict[str, int]
    intents: dict[str, int]
    last_updated_at: datetime | None


class FeedbackService:
    def __init__(
        self,
        data_path: Path | None = None,
    ) -> None:
        configured_path = os.getenv(
            "FEEDBACK_DATA_PATH"
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
            tuple[str, str],
            FeedbackRecord,
        ] = {}

        self._prepare_storage()
        self._load_existing_records()

    def submit_feedback(
        self,
        message_id: str,
        conversation_id: str | None,
        rating: FeedbackRating,
        reason: FeedbackReason | None,
        comment: str | None,
        intent: ChatIntent | None,
        metadata: dict[str, Any],
    ) -> FeedbackRecord:
        normalized_message_id = (
            message_id.strip()
        )

        normalized_conversation_id = (
            conversation_id.strip()
            if conversation_id
            else None
        )

        normalized_comment = (
            comment.strip()
            if comment and comment.strip()
            else None
        )

        if not normalized_message_id:
            raise ValueError(
                "Message ID cannot be empty."
            )

        key = self._build_key(
            conversation_id=(
                normalized_conversation_id
            ),
            message_id=normalized_message_id,
        )

        now = datetime.now(timezone.utc)

        with self._lock:
            existing = self._records.get(key)

            if existing is None:
                feedback_id = str(uuid4())
                created_at = now
            else:
                feedback_id = existing.feedback_id
                created_at = existing.created_at

            record = FeedbackRecord(
                feedback_id=feedback_id,
                message_id=normalized_message_id,
                conversation_id=(
                    normalized_conversation_id
                ),
                rating=rating,
                reason=reason,
                comment=normalized_comment,
                intent=intent,
                metadata=dict(metadata),
                created_at=created_at,
                updated_at=now,
            )

            self._records[key] = record
            self._append_record(record)

        return record

    def get_summary(
        self,
    ) -> FeedbackSummary:
        with self._lock:
            records = list(
                self._records.values()
            )

        thumbs_up = sum(
            1
            for record in records
            if record.rating
            == FeedbackRating.UP
        )

        thumbs_down = sum(
            1
            for record in records
            if record.rating
            == FeedbackRating.DOWN
        )

        total = len(records)

        approval_rate = (
            round(thumbs_up / total, 4)
            if total
            else None
        )

        reasons: dict[str, int] = {}
        intents: dict[str, int] = {}

        for record in records:
            if record.reason is not None:
                reason_key = record.reason.value

                reasons[reason_key] = (
                    reasons.get(reason_key, 0)
                    + 1
                )

            if record.intent is not None:
                intent_key = record.intent.value

                intents[intent_key] = (
                    intents.get(intent_key, 0)
                    + 1
                )

        last_updated_at = (
            max(
                record.updated_at
                for record in records
            )
            if records
            else None
        )

        return FeedbackSummary(
            total=total,
            thumbs_up=thumbs_up,
            thumbs_down=thumbs_down,
            approval_rate=approval_rate,
            reasons=reasons,
            intents=intents,
            last_updated_at=last_updated_at,
        )

    def _build_key(
        self,
        conversation_id: str | None,
        message_id: str,
    ) -> tuple[str, str]:
        return (
            conversation_id or "",
            message_id,
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
        record: FeedbackRecord,
    ) -> None:
        serialized = self._serialize_record(
            record
        )

        with self._data_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    serialized,
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

                key = self._build_key(
                    conversation_id=(
                        record.conversation_id
                    ),
                    message_id=(
                        record.message_id
                    ),
                )

                existing = self._records.get(
                    key
                )

                if (
                    existing is None
                    or record.updated_at
                    >= existing.updated_at
                ):
                    self._records[key] = record

    def _serialize_record(
        self,
        record: FeedbackRecord,
    ) -> dict[str, Any]:
        return {
            "feedback_id": (
                record.feedback_id
            ),
            "message_id": record.message_id,
            "conversation_id": (
                record.conversation_id
            ),
            "rating": record.rating.value,
            "reason": (
                record.reason.value
                if record.reason
                else None
            ),
            "comment": record.comment,
            "intent": (
                record.intent.value
                if record.intent
                else None
            ),
            "metadata": record.metadata,
            "created_at": (
                record.created_at.isoformat()
            ),
            "updated_at": (
                record.updated_at.isoformat()
            ),
        }

    def _deserialize_record(
        self,
        payload: dict[str, Any],
    ) -> FeedbackRecord:
        raw_reason = payload.get("reason")
        raw_intent = payload.get("intent")
        raw_metadata = payload.get(
            "metadata",
            {},
        )

        if not isinstance(raw_metadata, dict):
            raw_metadata = {}

        return FeedbackRecord(
            feedback_id=str(
                payload["feedback_id"]
            ),
            message_id=str(
                payload["message_id"]
            ),
            conversation_id=(
                str(payload["conversation_id"])
                if payload.get(
                    "conversation_id"
                )
                else None
            ),
            rating=FeedbackRating(
                payload["rating"]
            ),
            reason=(
                FeedbackReason(raw_reason)
                if raw_reason
                else None
            ),
            comment=(
                str(payload["comment"])
                if payload.get("comment")
                else None
            ),
            intent=(
                ChatIntent(raw_intent)
                if raw_intent
                else None
            ),
            metadata=dict(raw_metadata),
            created_at=datetime.fromisoformat(
                payload["created_at"]
            ),
            updated_at=datetime.fromisoformat(
                payload["updated_at"]
            ),
        )

    def _default_data_path(
        self,
    ) -> Path:
        return (
            Path(__file__).resolve().parents[1]
            / "data"
            / "feedback_events.jsonl"
        )


feedback_service = FeedbackService()
