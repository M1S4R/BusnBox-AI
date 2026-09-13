import re
from dataclasses import dataclass, field
from typing import Any, ClassVar

from app.schemas.chat import ChatParameters
from app.services.date_service import extract_date_reference


@dataclass
class QueryRefinementResult:
    parameters: ChatParameters
    removed_filters: list[str] = field(default_factory=list)
    sort_by: str | None = None
    sort_order: str = "asc"
    was_refinement: bool = False
    refinement_summary: str | None = None


class QueryRefinementService:
    FILTER_ALIASES: ClassVar[dict[str, str]] = {
        "price": "maximum_price",
        "fare": "maximum_price",
        "budget": "maximum_price",
        "operator": "operator",
        "company": "operator",
        "volvo": "bus_type",
        "bus type": "bus_type",
        "type": "bus_type",
        "sleeper": "bus_type",
        "seater": "bus_type",
        "ac": "bus_type",
        "seat": "minimum_seats",
        "seats": "minimum_seats",
        "departure": "departure_time",
        "time": "departure_time",
        "morning": "departure_time",
        "afternoon": "departure_time",
        "evening": "departure_time",
        "night": "departure_time",
    }

    def refine(
        self,
        message: str,
        current: ChatParameters,
        incoming: ChatParameters,
    ) -> QueryRefinementResult:
        normalized = self._normalize(message)

        current_filters = dict(current.filters or {})
        incoming_filters = dict(
            incoming.filters or {}
        )

        filters = {
            **current_filters,
            **incoming_filters,
        }

        removed_filters = self._remove_requested_filters(
            message=normalized,
            filters=filters,
        )

        changed_items: list[str] = []

        if self._apply_price_filter(
            message=normalized,
            filters=filters,
            current_filters=current_filters,
        ):
            changed_items.append("price")

        if self._apply_bus_type_filter(
            message=normalized,
            filters=filters,
        ):
            changed_items.append("bus type")

        if self._apply_operator_filter(
            message=normalized,
            filters=filters,
        ):
            changed_items.append("operator")

        if self._apply_departure_filter(
            message=normalized,
            filters=filters,
        ):
            changed_items.append(
                "departure time"
            )

        travel_date = self._resolve_date_reference(
            message=normalized,
            current_date=current.travel_date,
            incoming_date=incoming.travel_date,
        )

        if (
            travel_date
            and travel_date != current.travel_date
        ):
            changed_items.append("travel date")

        sort_by, sort_order = self._extract_sorting(
            normalized
        )

        if sort_by:
            changed_items.append("sorting")

        parameters = ChatParameters(
            source=(
                incoming.source
                if incoming.source is not None
                else current.source
            ),
            destination=(
                incoming.destination
                if incoming.destination is not None
                else current.destination
            ),
            travel_date=travel_date,
            filters=filters,
        )

        was_refinement = bool(
            removed_filters
            or changed_items
            or incoming.filters
            or self._looks_like_refinement(
                normalized
            )
        )

        summary = self._build_refinement_summary(
            removed_filters=removed_filters,
            changed_items=changed_items,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return QueryRefinementResult(
            parameters=parameters,
            removed_filters=removed_filters,
            sort_by=sort_by,
            sort_order=sort_order,
            was_refinement=was_refinement,
            refinement_summary=summary,
        )

    @staticmethod
    def _normalize(message: str) -> str:
        return " ".join(
            message.strip().lower().split()
        )

    def _remove_requested_filters(
        self,
        message: str,
        filters: dict[str, Any],
    ) -> list[str]:
        clear_all_phrases = (
            "remove all filters",
            "clear all filters",
            "reset all filters",
            "without any filters",
            "show all buses",
            "show everything",
            "remove filters",
            "clear filters",
            "reset filters",
            "clear that filter",
            "remove that filter",
            "clear filter",
            "remove filter",
        )

        if any(
            phrase in message
            for phrase in clear_all_phrases
        ):
            removed = list(filters.keys())
            filters.clear()
            return removed

        remove_words = (
            "remove",
            "clear",
            "delete",
            "without",
            "ignore",
            "no ",
            "not ",
            "don't filter",
            "dont filter",
            "don't show",
            "dont show",
            "except",
            "anything except",
        )

        if not any(
            phrase in message
            for phrase in remove_words
        ):
            return []

        removed: list[str] = []

        for alias, filter_name in (
            self.FILTER_ALIASES.items()
        ):
            if alias not in message:
                continue

            if filter_name in filters:
                filters.pop(
                    filter_name,
                    None,
                )

                if filter_name not in removed:
                    removed.append(filter_name)

        return removed

    @staticmethod
    def _apply_price_filter(
        message: str,
        filters: dict[str, Any],
        current_filters: dict[str, Any],
    ) -> bool:
        # 1. Price ranges: e.g. "between 500 and 800", "500 to 800"
        range_match = re.search(
            r"(?:between\s+)?(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:and|to|-)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)",
            message,
        )
        if range_match and any(
            k in message
            for k in ("between", "under", "below", "price", "fare", "budget", "rs", "inr", "₹", "range")
        ):
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            if high < low:
                low, high = high, low
            filters["minimum_price"] = int(low) if low.is_integer() else low
            filters["maximum_price"] = int(high) if high.is_integer() else high
            return True

        patterns = (
            (
                r"(?:under|below|less than|maximum|max|within)"
                r"\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)"
            ),
            (
                r"(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)"
                r"\s*(?:or less|maximum|max)"
            ),
            r"below\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                message,
            )

            if match is None:
                continue

            value = float(match.group(1))

            filters["maximum_price"] = (
                int(value)
                if value.is_integer()
                else value
            )

            return True

        cheaper_phrases = (
            "cheaper",
            "cheaper ones",
            "something cheaper",
            "lower price",
            "lower fare",
            "reduce the price",
            "more affordable",
        )

        if any(
            phrase in message
            for phrase in cheaper_phrases
        ):
            current_price = current_filters.get(
                "maximum_price"
            )

            if isinstance(
                current_price,
                (int, float),
            ):
                reduced_price = max(
                    int(current_price * 0.8),
                    100,
                )
                filters[
                    "maximum_price"
                ] = reduced_price

            return True

        return False

    @staticmethod
    def _apply_bus_type_filter(
        message: str,
        filters: dict[str, Any],
    ) -> bool:
        # Exclusion / removal checks first:
        volvo_exclusion = (
            "except volvo",
            "except for volvo",
            "don't show volvo",
            "dont show volvo",
            "no volvo",
            "without volvo",
            "remove volvo",
            "clear volvo",
            "not volvo",
            "anything except volvo",
        )
        if any(phrase in message for phrase in volvo_exclusion):
            if filters.get("bus_type") == "Volvo":
                filters.pop("bus_type", None)
            return False

        ac_removal = (
            "remove ac filter",
            "remove the ac filter",
            "clear ac filter",
            "clear the ac filter",
            "don't filter by ac",
            "dont filter by ac",
            "remove ac",
            "clear ac",
        )
        if any(phrase in message for phrase in ac_removal):
            if filters.get("bus_type") in {"AC", "Non-AC", "AC sleeper", "Non-AC sleeper"}:
                filters.pop("bus_type", None)
            return False

        bus_types = (
            (
                (
                    "non ac sleeper",
                    "non-ac sleeper",
                ),
                "Non-AC sleeper",
            ),
            (
                (
                    "ac sleeper",
                    "a/c sleeper",
                ),
                "AC sleeper",
            ),
            (
                (
                    "semi sleeper",
                    "semi-sleeper",
                ),
                "Semi sleeper",
            ),
            (
                (
                    "electric bus",
                    "electric buses",
                ),
                "Electric",
            ),
            (
                (
                    "non ac",
                    "non-ac",
                    "not ac",
                    "no ac",
                    "without ac",
                    "anything except ac",
                    "except ac",
                ),
                "Non-AC",
            ),
            (
                (
                    "ac buses",
                    "ac bus",
                    "only ac",
                    "with ac",
                    "a/c bus",
                    "i want ac",
                    "show ac buses",
                    "show ac",
                    "ac options",
                ),
                "AC",
            ),
            (
                (
                    "sleeper buses",
                    "sleeper bus",
                    "only sleeper",
                    "sleepers",
                    "show sleeper",
                    "show sleeper buses",
                ),
                "Sleeper",
            ),
            (
                (
                    "seater buses",
                    "seater bus",
                    "only seater",
                    "seaters",
                    "show seater",
                    "show seater buses",
                ),
                "Seater",
            ),
            (
                (
                    "only volvo",
                    "volvo buses",
                    "volvo bus",
                    "show volvo",
                    "volvo",
                ),
                "Volvo",
            ),
        )

        for keywords, value in bus_types:
            if any(
                keyword in message
                for keyword in keywords
            ):
                filters["bus_type"] = value
                return True

        return False

    @staticmethod
    def _apply_operator_filter(
        message: str,
        filters: dict[str, Any],
    ) -> bool:
        operator_patterns = (
            (
                r"(?:only|show|operator)\s+"
                r"([a-z][a-z0-9 &.-]{2,30})"
                r"(?:\s+buses?)?$"
            ),
            (
                r"(?:buses?\s+by|from operator)\s+"
                r"([a-z][a-z0-9 &.-]{2,30})$"
            ),
        )

        blocked_values = {
            "ac",
            "non ac",
            "sleeper",
            "seater",
            "volvo",
            "cheapest",
            "the cheapest",
            "cheaper",
            "cheap",
            "earliest",
            "the earliest",
            "earlier",
            "early",
            "latest",
            "the latest",
            "later",
            "late",
            "evening",
            "morning",
            "night",
            "afternoon",
            "best",
            "the best",
            "top",
            "fastest",
            "the fastest",
        }

        for pattern in operator_patterns:
            match = re.search(
                pattern,
                message,
            )

            if match is None:
                continue

            candidate = match.group(1).strip().lower()

            if candidate.startswith("me "):
                candidate = candidate[3:].strip()

            candidate = re.sub(
                r"\s+buses?$",
                "",
                candidate,
            ).strip()

            candidate = re.sub(
                r"\s+please$",
                "",
                candidate,
            ).strip()

            # An operator name should not contain numbers
            if re.search(r"\d", candidate):
                continue

            if (
                candidate in blocked_values
                or candidate.removeprefix("the ").strip() in blocked_values
                or any(
                    term in candidate.split()
                    for term in (
                        "ac",
                        "non",
                        "sleeper",
                        "seater",
                        "cheap",
                        "cheapest",
                        "early",
                        "earliest",
                        "late",
                        "latest",
                        "best",
                        "fast",
                        "fastest",
                        "volvo",
                        "filter",
                        "filters",
                        "please",
                        "something",
                        "anything",
                        "under",
                        "below",
                        "between",
                        "price",
                        "fare",
                        "budget",
                        "option",
                        "options",
                        "all",
                        "buses",
                        "bus",
                    )
                )
            ):
                continue

            filters["operator"] = (
                candidate.title()
            )
            return True

        return False

    @staticmethod
    def _apply_departure_filter(
        message: str,
        filters: dict[str, Any],
    ) -> bool:
        dayparts = {
            "early morning": "05:00",
            "morning": "06:00",
            "afternoon": "12:00",
            "evening": "17:00",
            "night": "20:00",
            "late night": "22:00",
        }

        for phrase, value in dayparts.items():
            if phrase in message:
                filters[
                    "departure_time"
                ] = value
                return True

        match = re.search(
            r"(?:after|later than|from)\s*"
            r"(\d{1,2})(?::(\d{2}))?\s*"
            r"(am|pm)?",
            message,
        )

        if match is not None:
            hour = int(match.group(1))
            minute = int(
                match.group(2) or 0
            )
            meridiem = match.group(3)

            if (
                meridiem == "pm"
                and hour != 12
            ):
                hour += 12

            if (
                meridiem == "am"
                and hour == 12
            ):
                hour = 0

            if hour <= 23 and minute <= 59:
                filters[
                    "departure_time"
                ] = (
                    f"{hour:02d}:"
                    f"{minute:02d}"
                )
                return True

        return False

    @staticmethod
    def _resolve_date_reference(
        message: str,
        current_date: str | None,
        incoming_date: str | None,
    ) -> str | None:
        extracted = extract_date_reference(message)
        if extracted is not None:
            return extracted

        if incoming_date is not None:
            return incoming_date

        return current_date

    @staticmethod
    def _extract_sorting(
        message: str,
    ) -> tuple[str | None, str]:
        cheapest_phrases = (
            "cheapest",
            "cheapest first",
            "lowest price",
            "lower price first",
            "low to high",
            "sort by price",
            "affordable first",
            "cheapest bus",
            "cheapest option",
            "lowest fare",
            "best price",
            "anything cheap",
            "something cheap",
            "cheapest one",
        )

        if any(
            phrase in message
            for phrase in cheapest_phrases
        ):
            return "price", "asc"

        expensive_phrases = (
            "most expensive",
            "highest price",
            "high to low",
            "premium first",
        )

        if any(
            phrase in message
            for phrase in expensive_phrases
        ):
            return "price", "desc"

        earliest_phrases = (
            "earliest",
            "earlier buses",
            "earlier ones",
            "earliest departure",
            "departure time ascending",
            "earliest bus",
            "earliest one",
            "fastest",
            "fastest bus",
            "which one is fastest",
        )

        if any(
            phrase in message
            for phrase in earliest_phrases
        ):
            return "departure_time", "asc"

        latest_phrases = (
            "latest",
            "later buses",
            "later ones",
            "latest departure",
            "departure time descending",
        )

        if any(
            phrase in message
            for phrase in latest_phrases
        ):
            return "departure_time", "desc"

        return None, "asc"

    @staticmethod
    def sort_trips(
        trips: list[dict[str, Any]],
        sort_by: str | None,
        sort_order: str = "asc",
    ) -> list[dict[str, Any]]:
        if not sort_by:
            return trips

        reverse = sort_order == "desc"

        if sort_by == "price":
            return sorted(
                trips,
                key=(
                    QueryRefinementService
                    ._price_value
                ),
                reverse=reverse,
            )

        if sort_by == "departure_time":
            return sorted(
                trips,
                key=(
                    QueryRefinementService
                    ._departure_value
                ),
                reverse=reverse,
            )

        return trips

    @staticmethod
    def _price_value(
        trip: dict[str, Any],
    ) -> float:
        candidates = [
            trip.get("price"),
            trip.get("fare"),
            trip.get("starting_price"),
            trip.get("minimum_price"),
        ]

        fares = trip.get("fares")

        if isinstance(fares, dict):
            candidates.extend(
                fares.values()
            )

        if isinstance(fares, list):
            candidates.extend(fares)

        for candidate in candidates:
            if isinstance(
                candidate,
                (int, float),
            ):
                return float(candidate)

            if isinstance(candidate, str):
                cleaned = re.sub(
                    r"[^\d.]",
                    "",
                    candidate,
                )

                try:
                    return float(cleaned)
                except ValueError:
                    continue

        return float("inf")

    @staticmethod
    def _departure_value(
        trip: dict[str, Any],
    ) -> str:
        candidates = [
            trip.get("departure_time"),
            trip.get("departure"),
            trip.get("start_time"),
        ]

        timings = trip.get("timings")

        if isinstance(timings, dict):
            candidates.extend(
                [
                    timings.get("departure"),
                    timings.get(
                        "departure_time"
                    ),
                ]
            )

        for candidate in candidates:
            if candidate is not None:
                return str(candidate)

        return "99:99"

    @staticmethod
    def _looks_like_refinement(
        message: str,
    ) -> bool:
        refinement_words = (
            "only",
            "under",
            "below",
            "after",
            "before",
            "cheaper",
            "affordable",
            "earlier",
            "later",
            "cheapest",
            "earliest",
            "latest",
            "sort",
            "remove",
            "clear",
            "reset",
            "without",
            "instead",
            "morning",
            "afternoon",
            "evening",
            "night",
        )

        return any(
            word in message
            for word in refinement_words
        )

    @staticmethod
    def _build_refinement_summary(
        removed_filters: list[str],
        changed_items: list[str],
        sort_by: str | None,
        sort_order: str,
    ) -> str | None:
        parts: list[str] = []

        if removed_filters:
            readable = ", ".join(
                item.replace("_", " ")
                for item in removed_filters
            )

            parts.append(
                f"Removed: {readable}"
            )

        if changed_items:
            unique_items = list(
                dict.fromkeys(changed_items)
            )

            readable = ", ".join(
                unique_items
            )

            parts.append(
                f"Updated: {readable}"
            )

        if sort_by:
            readable_sort = sort_by.replace(
                "_",
                " ",
            )

            direction = (
                "ascending"
                if sort_order == "asc"
                else "descending"
            )

            parts.append(
                f"Sorted by {readable_sort} "
                f"in {direction} order"
            )

        if not parts:
            return None

        return ". ".join(parts) + "."


query_refinement_service = (
    QueryRefinementService()
)
