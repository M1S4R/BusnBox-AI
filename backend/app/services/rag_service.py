import re
from dataclasses import dataclass
from typing import ClassVar

from app.ai.providers.base_provider import BaseLLMProvider
from app.ai.providers.provider_factory import ProviderFactory
from app.services.knowledge_base_service import (
    KnowledgeBaseService,
    KnowledgeMatch,
    knowledge_base_service,
)


class RAGServiceError(RuntimeError):
    """Raised when the grounded-answer service fails."""


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    source_ids: tuple[str, ...]
    source_titles: tuple[str, ...]
    confidence: float


class RAGService:
    MIN_GROUNDING_SCORE: ClassVar[float] = 0.35

    _INSUFFICIENT_RESPONSE: ClassVar[str] = "INSUFFICIENT_KNOWLEDGE"

    _SAFE_FALLBACK: ClassVar[str] = (
        "I don't have enough verified BusNBox "
        "information to answer that reliably."
    )

    _SUPPORT_TERMS: ClassVar[set[str]] = {
        "refund",
        "refunds",
        "cancel",
        "cancelled",
        "cancellation",
        "payment",
        "payments",
        "deducted",
        "transaction",
        "transactions",
        "luggage",
        "baggage",
        "bag",
        "bags",
        "pet",
        "pets",
        "dog",
        "cat",
        "child",
        "children",
        "infant",
        "seat",
        "seats",
        "boarding",
        "document",
        "documents",
        "identity",
        "proof",
        "reschedule",
        "rescheduling",
        "change",
        "changes",
        "policy",
        "policies",
        "miss",
        "missed",
        "late",
        "confirmation",
        "confirmed",
        "wallet",
        "upi",
        "ticket",
        "tickets",
        "booking",
        "bookings",
        "book",
        "charge",
        "charges",
        "fee",
        "fees",
        "delay",
        "delayed",
    }

    _ACTION_REQUEST_PHRASES: ClassVar[tuple[str, ...]] = (
        "confirm my booking",
        "confirm booking",
        "confirm my ticket",
        "confirm ticket",
        "book my bus",
        "book a bus",
        "book the bus",
        "book the cheapest bus",
        "book cheapest bus",
        "make a booking",
        "make booking",
        "create a booking",
        "create booking",
        "cancel my booking",
        "cancel my ticket",
        "cancel booking",
        "cancel ticket",
        "refund my booking",
        "refund my ticket",
        "process my refund",
        "process refund",
        "reschedule my booking",
        "reschedule my ticket",
        "change my booking",
        "change my ticket",
        "pay for my booking",
        "pay for my ticket",
        "complete my payment",
        "complete payment",
    )

    _UNSAFE_PHRASES: ClassVar[tuple[str, ...]] = (
        "i assume",
        "i think",
        "probably",
        "likely",
        "it may be",
        "it might be",
        "generally",
        "usually",
        "in most cases",
        "as far as i know",
        "according to general policy",
        "typically",
        "normally",
    )

    _ACTION_CLAIMS: ClassVar[tuple[str, ...]] = (
        "booking has been confirmed",
        "booking is confirmed",
        "booking was confirmed",
        "successfully confirmed",
        "reservation has been confirmed",
        "reservation is confirmed",
        "ticket has been booked",
        "ticket is booked",
        "booking has been cancelled",
        "booking is cancelled",
        "refund has been processed",
        "refund has been issued",
        "payment has been completed",
        "payment was completed",
        "reschedule has been completed",
        "rescheduling has been completed",
    )

    def __init__(
        self,
        knowledge_service: KnowledgeBaseService | None = None,
        provider: BaseLLMProvider | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._knowledge_service = (
            knowledge_service or knowledge_base_service
        )
        self._provider = provider or ProviderFactory.get_provider()

    async def answer(self, question: str) -> RAGAnswer | None:
        normalized_question = question.strip()

        if not normalized_question:
            return None

        if self._looks_like_action_request(normalized_question):
            return None

        if self._looks_like_trip_search(normalized_question):
            return None

        if not self._looks_like_support_question(normalized_question):
            return None

        matches = self._knowledge_service.search(
            query=normalized_question,
            limit=3,
            minimum_score=0.22,
        )

        if not matches:
            return None

        if not self._has_sufficient_grounding(
            matches=matches,
            question=normalized_question,
        ):
            return None

        context = self._knowledge_service.build_context(matches)

        if not context.strip():
            return None

        prompt = self._build_prompt(
            question=normalized_question,
            context=context,
        )

        generated_answer = await self._generate_answer(prompt)

        cleaned_answer = self._clean_answer(generated_answer)

        fallback = self._build_grounded_fallback(matches)

        if (
            not cleaned_answer
            or self._is_insufficient_response(cleaned_answer)
        ):
            return self._build_answer(
                matches=matches,
                answer=fallback,
            )

        if self._is_unsafe_answer(cleaned_answer):
            return self._build_answer(
                matches=matches,
                answer=fallback,
            )

        if not self._has_contextual_support(
            answer=cleaned_answer,
            context=context,
        ):
            return self._build_answer(
                matches=matches,
                answer=fallback,
            )

        return self._build_answer(
            matches=matches,
            answer=cleaned_answer,
        )

    def _build_answer(
        self,
        *,
        matches: list[KnowledgeMatch],
        answer: str,
    ) -> RAGAnswer:
        return RAGAnswer(
            answer=answer,
            source_ids=tuple(
                match.document_id
                for match in matches
            ),
            source_titles=tuple(
                match.title
                for match in matches
            ),
            confidence=self._calculate_confidence(matches),
        )

    def _has_sufficient_grounding(
        self,
        matches: list[KnowledgeMatch],
        question: str,
    ) -> bool:
        if not matches:
            return False

        top_match = matches[0]
        score = top_match.score

        if not isinstance(score, (int, float)):
            return False

        if score >= self.MIN_GROUNDING_SCORE:
            return True

        question_tokens = self._meaningful_tokens(question)
        content_tokens = self._meaningful_tokens(
            top_match.content
        )

        overlap = question_tokens & content_tokens

        return len(overlap) >= 2

    def _is_unsafe_answer(self, answer: str) -> bool:
        return (
            self._contains_unsafe_language(answer)
            or self._contains_action_claim(answer)
            or self._contains_suspicious_numeric_claim(answer)
        )

    def _contains_unsafe_language(self, answer: str) -> bool:
        normalized = self._normalize_text(answer)

        return any(
            phrase in normalized
            for phrase in self._UNSAFE_PHRASES
        )

    def _contains_action_claim(self, answer: str) -> bool:
        normalized = self._normalize_text(answer)

        return any(
            phrase in normalized
            for phrase in self._ACTION_CLAIMS
        )

    def _contains_suspicious_numeric_claim(
        self,
        answer: str,
    ) -> bool:
        normalized = answer.casefold()

        currency_pattern = re.compile(
            r"(?:₹|\$|€|£)\s*\d+|(?:rs\.?|inr)\s*\d+",
            re.IGNORECASE,
        )

        if currency_pattern.search(normalized):
            return True

        if re.search(
            r"\b\d+(?:\.\d+)?\s*%",
            normalized,
        ):
            return True

        duration_pattern = re.compile(
            r"\b\d+\s+(?:minutes?|hours?|days?|weeks?|months?)\b",
            re.IGNORECASE,
        )

        return bool(
            duration_pattern.search(normalized)
        )

    def _is_insufficient_response(
        self,
        answer: str,
    ) -> bool:
        normalized = answer.strip().upper()

        return self._INSUFFICIENT_RESPONSE in normalized

    def _has_contextual_support(
        self,
        *,
        answer: str,
        context: str,
    ) -> bool:
        answer_tokens = self._meaningful_tokens(answer)
        context_tokens = self._meaningful_tokens(context)

        if not answer_tokens:
            return False

        if not context_tokens:
            return False

        overlap = answer_tokens & context_tokens

        if len(answer_tokens) <= 5:
            return bool(overlap)

        return len(overlap) >= 2

    def _meaningful_tokens(
        self,
        value: str,
    ) -> set[str]:
        normalized = self._normalize_text(value)

        stop_words = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "can",
            "could",
            "do",
            "does",
            "for",
            "from",
            "how",
            "i",
            "if",
            "in",
            "is",
            "it",
            "me",
            "my",
            "of",
            "on",
            "or",
            "please",
            "the",
            "this",
            "to",
            "what",
            "when",
            "where",
            "which",
            "with",
            "you",
            "your",
        }

        return {
            token
            for token in normalized.split()
            if len(token) >= 3
            and token not in stop_words
        }

    async def _generate_answer(
        self,
        prompt: str,
    ) -> str:
        try:
            return await self._provider.generate(
                prompt,
                system_instruction=(
                    "You are BnB AI, the BusNBox travel "
                    "assistant. Answer only using the "
                    "verified information supplied in "
                    "the prompt. Never invent facts, "
                    "prices, policies, durations, or "
                    "completed actions."
                ),
            )
        except Exception as exc:
            raise RAGServiceError(
                "Gemini failed while generating "
                "the grounded knowledge answer."
            ) from exc

    def _build_prompt(
        self,
        question: str,
        context: str,
    ) -> str:
        return f"""
You are BnB AI, the BusNBox travel assistant.

Answer the user's question using ONLY the supplied
BusNBox knowledge-base information.

STRICT GROUNDING RULES:

1. Use ONLY facts explicitly supported by the supplied
   information.

2. Do NOT use outside knowledge.

3. Do NOT guess, infer, estimate, assume, or complete
   missing information.

4. Do NOT invent policies, prices, fees, deadlines,
   refund durations, cancellation rules, guarantees,
   eligibility requirements, operator rules, or
   booking conditions.

5. If a specific detail is not present in the supplied
   information, do not state that detail as fact.

6. If the supplied information is insufficient to answer
   the question, respond with exactly:
   {self._INSUFFICIENT_RESPONSE}

7. Only state operator-specific rules when explicitly
   supported by the supplied information.

8. Do not claim that a booking, cancellation, refund,
   payment, reschedule, or other action has been completed.

9. Do not make promises about future availability,
   refunds, confirmations, or service outcomes.

10. Do not invent numerical values such as prices,
    percentages, fees, durations, or deadlines.

11. Keep the answer concise.

12. Do not mention prompts, retrieval, RAG, models,
    documents, context, or knowledge bases.

13. Return only the answer.

BUSNBOX DOCUMENTS:
{context}

USER QUESTION:
{question}

GROUNDED ANSWER:
""".strip()

    def _build_grounded_fallback(
        self,
        matches: list[KnowledgeMatch],
    ) -> str:
        if not matches:
            return self._SAFE_FALLBACK

        primary_match = matches[0]
        content = primary_match.content.strip()

        if not content:
            return self._SAFE_FALLBACK

        if content.upper() == self._INSUFFICIENT_RESPONSE:
            return self._SAFE_FALLBACK

        return content

    def _looks_like_action_request(
        self,
        question: str,
    ) -> bool:
        normalized = self._normalize_text(question)

        return any(
            phrase in normalized
            for phrase in self._ACTION_REQUEST_PHRASES
        )

    def _looks_like_support_question(
        self,
        question: str,
    ) -> bool:
        normalized = self._normalize_text(question)
        tokens = set(normalized.split())

        return bool(
            tokens & self._SUPPORT_TERMS
        )

    def _looks_like_trip_search(
        self,
        question: str,
    ) -> bool:
        normalized = self._normalize_text(question)

        direct_search_phrases = (
            "find bus",
            "find buses",
            "show bus",
            "show buses",
            "search bus",
            "search buses",
            "available bus",
            "available buses",
            "bus from",
            "buses from",
        )

        if any(
            phrase in normalized
            for phrase in direct_search_phrases
        ):
            return True

        has_route_pattern = bool(
            re.search(
                r"\bfrom\s+.+\s+to\s+.+",
                normalized,
            )
        )

        has_date_term = any(
            term in normalized.split()
            for term in (
                "today",
                "tomorrow",
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            )
        )

        return (
            has_route_pattern
            and has_date_term
        )

    def _calculate_confidence(
        self,
        matches: list[KnowledgeMatch],
    ) -> float:
        if not matches:
            return 0.0

        top_score = matches[0].score

        if not isinstance(top_score, (int, float)):
            return 0.0

        return round(
            min(
                max(float(top_score), 0.0),
                1.0,
            ),
            2,
        )

    def _clean_answer(
        self,
        answer: str,
    ) -> str:
        cleaned = answer.strip()

        cleaned = re.sub(
            r"^```(?:text|markdown)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

        return cleaned.strip()

    def _normalize_text(
        self,
        value: str,
    ) -> str:
        lowered = value.casefold().strip()

        cleaned = re.sub(
            r"[^a-z0-9\s]",
            " ",
            lowered,
        )

        return re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()


rag_service = RAGService()