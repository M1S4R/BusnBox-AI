import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FAQEntry:
    id: str
    question: str
    answer: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class FAQMatch:
    faq_id: str
    question: str
    answer: str
    confidence: float
    matched_keywords: tuple[str, ...]


class FAQService:
    def __init__(self) -> None:
        self._entries = self._build_entries()

    def find_answer(
        self,
        message: str,
    ) -> FAQMatch | None:
        normalized_message = self._normalize_text(
            message
        )

        if not normalized_message:
            return None

        message_tokens = set(
            normalized_message.split()
        )

        best_entry: FAQEntry | None = None
        best_keywords: tuple[str, ...] = ()
        best_score = 0.0

        for entry in self._entries:
            matched_keywords = tuple(
                keyword
                for keyword in entry.keywords
                if self._keyword_matches(
                    keyword=keyword,
                    normalized_message=(
                        normalized_message
                    ),
                    message_tokens=message_tokens,
                )
            )

            score = self._calculate_score(
                entry=entry,
                matched_keywords=matched_keywords,
                normalized_message=(
                    normalized_message
                ),
            )

            if score > best_score:
                best_entry = entry
                best_keywords = matched_keywords
                best_score = score

        if best_entry is None:
            return None

        if best_score < 0.25:
            return None

        return FAQMatch(
            faq_id=best_entry.id,
            question=best_entry.question,
            answer=best_entry.answer,
            confidence=round(
                min(best_score, 1.0),
                2,
            ),
            matched_keywords=best_keywords,
        )

    def get_all_questions(self) -> list[str]:
        return [
            entry.question
            for entry in self._entries
        ]

    def _keyword_matches(
        self,
        keyword: str,
        normalized_message: str,
        message_tokens: set[str],
    ) -> bool:
        normalized_keyword = self._normalize_text(
            keyword
        )

        if " " in normalized_keyword:
            return (
                normalized_keyword
                in normalized_message
            )

        return normalized_keyword in message_tokens

    def _calculate_score(
        self,
        entry: FAQEntry,
        matched_keywords: tuple[str, ...],
        normalized_message: str,
    ) -> float:
        if not matched_keywords:
            return 0.0

        keyword_score = (
            len(matched_keywords)
            / max(len(entry.keywords), 1)
        )

        question_text = self._normalize_text(
            entry.question
        )

        question_tokens = set(
            question_text.split()
        )

        message_tokens = set(
            normalized_message.split()
        )

        overlap = (
            question_tokens
            & message_tokens
        )

        question_overlap_score = (
            len(overlap)
            / max(len(question_tokens), 1)
        )

        phrase_bonus = 0.0

        for keyword in matched_keywords:
            if " " in keyword:
                phrase_bonus += 0.15

        return (
            keyword_score * 0.70
            + question_overlap_score * 0.30
            + phrase_bonus
        )

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

    def _build_entries(
        self,
    ) -> tuple[FAQEntry, ...]:
        return (
            FAQEntry(
                id="faq-book-ticket",
                question=(
                    "How can I book a bus ticket?"
                ),
                answer=(
                    "Search for buses by entering your "
                    "source, destination, and travel date. "
                    "Choose a suitable bus, select your "
                    "seat, enter the passenger details, "
                    "and complete the payment. Your booking "
                    "confirmation will be shown after the "
                    "payment succeeds."
                ),
                keywords=(
                    "book ticket",
                    "booking",
                    "reserve seat",
                    "buy ticket",
                    "how to book",
                ),
            ),
            FAQEntry(
                id="faq-cancel-ticket",
                question=(
                    "How can I cancel my bus ticket?"
                ),
                answer=(
                    "Open your booking details and select "
                    "the cancellation option. Cancellation "
                    "charges depend on the bus operator and "
                    "how close the request is to the "
                    "departure time. Review the displayed "
                    "refund amount before confirming."
                ),
                keywords=(
                    "cancel ticket",
                    "cancellation",
                    "cancel booking",
                    "cancel seat",
                    "cancel",
                ),
            ),
            FAQEntry(
                id="faq-refund-time",
                question=(
                    "When will I receive my refund?"
                ),
                answer=(
                    "After an eligible cancellation or "
                    "failed payment, the refund is processed "
                    "to the original payment method. The "
                    "time required depends on the bank or "
                    "payment provider. Check your booking "
                    "or payment status for the latest update."
                ),
                keywords=(
                    "refund",
                    "refund time",
                    "money back",
                    "refund status",
                    "receive refund",
                ),
            ),
            FAQEntry(
                id="faq-payment-failed",
                question=(
                    "What happens if my payment fails?"
                ),
                answer=(
                    "A booking is confirmed only when the "
                    "payment succeeds and a confirmation is "
                    "generated. If money was deducted but "
                    "the booking was not confirmed, verify "
                    "the payment status before trying again. "
                    "Any eligible reversal is normally sent "
                    "to the original payment method."
                ),
                keywords=(
                    "payment failed",
                    "money deducted",
                    "transaction failed",
                    "payment issue",
                    "booking not confirmed",
                ),
            ),
            FAQEntry(
                id="faq-payment-methods",
                question=(
                    "Which payment methods are supported?"
                ),
                answer=(
                    "Available payment methods may include "
                    "UPI, debit cards, credit cards, net "
                    "banking, and supported digital wallets. "
                    "The exact options are displayed during "
                    "checkout."
                ),
                keywords=(
                    "payment methods",
                    "upi",
                    "credit card",
                    "debit card",
                    "net banking",
                    "wallet",
                    "pay",
                ),
            ),
            FAQEntry(
                id="faq-luggage",
                question=(
                    "How much luggage can I carry?"
                ),
                answer=(
                    "Luggage limits are decided by the bus "
                    "operator. Normal personal luggage is "
                    "usually permitted, but oversized, "
                    "commercial, hazardous, or restricted "
                    "items may not be allowed. Check the "
                    "operator policy shown with the trip."
                ),
                keywords=(
                    "luggage",
                    "baggage",
                    "bags",
                    "suitcase",
                    "carry luggage",
                ),
            ),
            FAQEntry(
                id="faq-child-ticket",
                question=(
                    "Does a child need a separate ticket?"
                ),
                answer=(
                    "Child ticket requirements depend on "
                    "the operator's age and seat policy. A "
                    "separate ticket is generally required "
                    "when the child uses a seat. Review the "
                    "operator policy before booking."
                ),
                keywords=(
                    "child ticket",
                    "children",
                    "kid",
                    "baby",
                    "child seat",
                    "infant",
                ),
            ),
            FAQEntry(
                id="faq-pets",
                question=(
                    "Can I travel with a pet?"
                ),
                answer=(
                    "Pet travel rules vary by bus operator. "
                    "Many operators do not permit pets, while "
                    "some may allow them under specific "
                    "conditions. Confirm the operator's pet "
                    "policy before completing the booking."
                ),
                keywords=(
                    "pet",
                    "pets",
                    "dog",
                    "cat",
                    "animal",
                    "pet policy",
                ),
            ),
            FAQEntry(
                id="faq-ticket-document",
                question=(
                    "What should I carry while boarding?"
                ),
                answer=(
                    "Carry your booking confirmation or "
                    "ticket and a valid government-issued "
                    "photo ID matching the passenger details. "
                    "Some operators may have additional "
                    "boarding requirements."
                ),
                keywords=(
                    "boarding document",
                    "photo id",
                    "identity proof",
                    "carry ticket",
                    "boarding",
                    "documents",
                ),
            ),
            FAQEntry(
                id="faq-seat-selection",
                question=(
                    "Why am I unable to select a seat?"
                ),
                answer=(
                    "Seat selection may be unavailable when "
                    "the operator assigns seats automatically, "
                    "the seat map has not loaded, or the "
                    "selected seats were booked by another "
                    "customer. Refresh the availability or "
                    "choose another bus."
                ),
                keywords=(
                    "select seat",
                    "seat unavailable",
                    "seat selection",
                    "choose seat",
                    "seat map",
                ),
            ),
            FAQEntry(
                id="faq-change-booking",
                question=(
                    "Can I change my travel date or bus?"
                ),
                answer=(
                    "Direct modification depends on the "
                    "operator's policy. When changes are not "
                    "supported, you may need to cancel the "
                    "existing booking and create a new one. "
                    "Check cancellation charges before doing "
                    "so."
                ),
                keywords=(
                    "change date",
                    "change bus",
                    "modify booking",
                    "reschedule",
                    "change ticket",
                    "change my ticket",
                    "modify ticket",
                ),
            ),
            FAQEntry(
                id="faq-missed-bus",
                question=(
                    "What happens if I miss my bus?"
                ),
                answer=(
                    "Passengers should arrive at the boarding point before "
                    "the reporting time shown on the ticket. If you miss the bus "
                    "due to late arrival, it may not qualify for a refund according "
                    "to the operator policy. Please check operator terms or "
                    "contact customer support."
                ),
                keywords=(
                    "missed bus",
                    "miss bus",
                    "missed my bus",
                    "miss my bus",
                    "late for bus",
                    "late boarding",
                ),
            ),
            FAQEntry(
                id="faq-booking-confirmation",
                question=(
                    "How do I know my booking is confirmed?"
                ),
                answer=(
                    "A successful booking returns a "
                    "confirmation containing the booking "
                    "reference, trip details, passenger "
                    "details, and boarding information. A "
                    "payment deduction alone does not always "
                    "mean that the booking was confirmed."
                ),
                keywords=(
                    "booking confirmed",
                    "confirmation",
                    "ticket confirmed",
                    "booking reference",
                    "confirmed ticket",
                ),
            ),
        )


faq_service = FAQService()
