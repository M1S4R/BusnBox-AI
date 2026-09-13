from __future__ import annotations

from datetime import date
from typing import Any

from app.schemas.chat import ChatParameters
from app.services.query_refinement_service import (
    QueryRefinementResult,
)


class ChatResponseService:
    """
    Builds deterministic, user-friendly responses from validated
    inventory results.

    This service does not call an LLM. It only describes data that
    already passed through the inventory adapter and Pydantic schemas.
    """

    def build_search_reply(
        self,
        *,
        parameters: ChatParameters,
        trips: list[dict[str, Any]],
        refinement: QueryRefinementResult | None = None,
        resolved_date: date | None = None,
    ) -> str:
        source = (
            parameters.source
            or "your departure city"
        )

        destination = (
            parameters.destination
            or "your destination"
        )

        travel_date = self._format_travel_date(
            original_value=parameters.travel_date,
            resolved_date=resolved_date,
        )

        if not trips:
            return self._build_no_results_reply(
                source=source,
                destination=destination,
                travel_date=travel_date,
                parameters=parameters,
                refinement=refinement,
            )

        count = len(trips)

        introduction = (
            self._build_result_introduction(
                count=count,
                source=source,
                destination=destination,
                travel_date=travel_date,
                refinement=refinement,
            )
        )

        highlights = self._build_trip_highlights(
            trips=trips,
        )

        active_filters = (
            self._build_filter_summary(
                parameters.filters or {}
            )
        )

        sections = [introduction]

        if highlights:
            sections.append(highlights)

        if active_filters:
            sections.append(
                f"Applied filters: {active_filters}."
            )

        return " ".join(sections)

    def build_missing_route_reply(self) -> str:
        return "Sure — where would you like to travel from and to?"

    def build_missing_source_reply(self) -> str:
        return (
            "Sure — where would you like to begin "
            "your journey?"
        )

    def build_missing_destination_reply(
        self,
        source: str | None,
    ) -> str:
        if source:
            return (
                f"Got it, departing from {source}. "
                "Where would you like to go?"
            )

        return (
            "Where would you like to travel to?"
        )

    def build_missing_date_reply(
        self,
        source: str | None,
        destination: str | None,
    ) -> str:
        if source and destination:
            return (
                f"When would you like to travel from "
                f"{source} to {destination}?"
            )

        return (
            "What date would you like to travel?"
        )

    def _build_result_introduction(
        self,
        *,
        count: int,
        source: str,
        destination: str,
        travel_date: str,
        refinement: QueryRefinementResult | None,
    ) -> str:
        bus_word = (
            "bus"
            if count == 1
            else "buses"
        )

        refinement_text = (
            self._build_refinement_prefix(
                refinement
            )
        )

        result_text = (
            f"I found {count} {bus_word} from "
            f"{source} to {destination} "
            f"{travel_date}."
        )

        if refinement_text:
            return (
                f"{refinement_text} "
                f"{result_text}"
            )

        return result_text

    def _build_no_results_reply(
        self,
        *,
        source: str,
        destination: str,
        travel_date: str,
        parameters: ChatParameters,
        refinement: QueryRefinementResult | None,
    ) -> str:
        refinement_text = (
            self._build_refinement_prefix(
                refinement
            )
        )

        filters = (
            self._build_filter_summary(
                parameters.filters or {}
            )
        )

        result = (
            f"I couldn't find any buses from "
            f"{source} to {destination} "
            f"{travel_date}"
        )

        if filters:
            result += (
                f" with {filters}"
            )

        result += "."

        suggestion = (
            " Try removing a filter, increasing "
            "your budget, or choosing another "
            "departure time."
        )

        if refinement_text:
            return (
                f"{refinement_text} "
                f"{result}{suggestion}"
            )

        return (
            f"{result}{suggestion}"
        )

    def _build_refinement_prefix(
        self,
        refinement: QueryRefinementResult | None,
    ) -> str | None:
        if refinement is None:
            return None

        phrases: list[str] = []

        if refinement.removed_filters:
            removed = self._human_join(
                [
                    self._filter_display_name(
                        name
                    )
                    for name in (
                        refinement.removed_filters
                    )
                ]
            )

            phrases.append(
                f"I removed the {removed} filter"
            )

        if refinement.sort_by == "price":
            if refinement.sort_order == "desc":
                phrases.append(
                    "I sorted the results from highest "
                    "to lowest price"
                )
            else:
                phrases.append(
                    "I sorted the cheapest options first"
                )

        elif refinement.sort_by == "departure_time":
            if refinement.sort_order == "desc":
                phrases.append(
                    "I sorted the latest departures first"
                )
            else:
                phrases.append(
                    "I sorted the earliest departures first"
                )

        if not phrases:
            return None

        return (
            f"{'. '.join(phrases)}."
        )

    def _build_trip_highlights(
        self,
        trips: list[dict[str, Any]],
    ) -> str | None:
        cheapest = (
            self._find_cheapest_trip(
                trips
            )
        )

        earliest = (
            self._find_earliest_trip(
                trips
            )
        )

        highlights: list[str] = []

        if cheapest is not None:
            operator = (
                self._extract_operator(
                    cheapest
                )
            )

            price = (
                self._extract_price(
                    cheapest
                )
            )

            if (
                operator
                and price is not None
            ):
                highlights.append(
                    f"The lowest fare is ₹{price:g} "
                    f"with {operator}"
                )

            elif price is not None:
                highlights.append(
                    f"The lowest fare is ₹{price:g}"
                )

        if earliest is not None:
            operator = (
                self._extract_operator(
                    earliest
                )
            )

            departure = (
                self._extract_departure(
                    earliest
                )
            )

            if (
                operator
                and departure
                and earliest is not cheapest
            ):
                highlights.append(
                    f"the earliest departure is "
                    f"{departure} with {operator}"
                )

            elif (
                departure
                and earliest is not cheapest
            ):
                highlights.append(
                    f"the earliest departure is "
                    f"{departure}"
                )

        if not highlights:
            return None

        return (
            f"{self._human_join(highlights).capitalize()}."
        )

    def _build_filter_summary(
        self,
        filters: dict[str, Any],
    ) -> str | None:
        descriptions: list[str] = []

        bus_type = filters.get(
            "bus_type"
        )

        if bus_type:
            descriptions.append(
                f"{bus_type} buses"
            )

        operator = filters.get(
            "operator"
        )

        if operator:
            descriptions.append(
                f"operator {operator}"
            )

        maximum_price = filters.get(
            "maximum_price"
        )

        if maximum_price is not None:
            descriptions.append(
                f"fares up to ₹{maximum_price}"
            )

        minimum_seats = filters.get(
            "minimum_seats"
        )

        if minimum_seats is not None:
            descriptions.append(
                f"at least {minimum_seats} seats"
            )

        departure_time = filters.get(
            "departure_time"
        )

        if departure_time:
            descriptions.append(
                f"departures after {departure_time}"
            )

        if not descriptions:
            return None

        return self._human_join(
            descriptions
        )

    @staticmethod
    def _format_travel_date(
        *,
        original_value: str | None,
        resolved_date: date | None,
    ) -> str:
        """
        Always prefer the deterministic resolved date.

        Example:
            original_value = "tomorrow"
            resolved_date = 2026-09-07

        Output:
            "on 07 Sep 2026"

        This prevents the response layer from hiding the actual
        resolved date behind words such as "tomorrow".
        """

        if resolved_date is not None:
            return (
                "on "
                f"{resolved_date.strftime('%d %b %Y')}"
            )

        if original_value:
            normalized = (
                original_value
                .strip()
                .lower()
            )

            if normalized == "today":
                return "today"

            if normalized == "tomorrow":
                return "tomorrow"

            return f"on {original_value}"

        return ""

    def _find_cheapest_trip(
        self,
        trips: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        priced_trips = [
            trip
            for trip in trips
            if self._extract_price(
                trip
            ) is not None
        ]

        if not priced_trips:
            return None

        return min(
            priced_trips,
            key=lambda trip: (
                self._extract_price(
                    trip
                )
                or float("inf")
            ),
        )

    def _find_earliest_trip(
        self,
        trips: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        timed_trips = [
            trip
            for trip in trips
            if self._extract_departure(
                trip
            )
        ]

        if not timed_trips:
            return None

        return min(
            timed_trips,
            key=lambda trip: (
                self._time_sort_value(
                    self._extract_departure(
                        trip
                    )
                )
            ),
        )

    @staticmethod
    def _extract_operator(
        trip: dict[str, Any],
    ) -> str | None:
        operator = (
            trip.get("operator")
            or trip.get("operator_name")
            or trip.get("bus_operator")
        )

        if operator is None:
            return None

        if isinstance(operator, dict):
            return operator.get("name") or operator.get("operator_name") or str(operator)

        return str(operator)

    @staticmethod
    def _extract_price(
        trip: dict[str, Any],
    ) -> float | None:
        candidates: list[Any] = [
            trip.get("price"),
            trip.get("fare"),
            trip.get("starting_price"),
            trip.get("minimum_price"),
        ]

        fares = trip.get("fares")

        if isinstance(
            fares,
            dict,
        ):
            candidates.extend(
                fares.values()
            )

        elif isinstance(
            fares,
            list,
        ):
            candidates.extend(
                fares
            )

        numeric_values: list[float] = []

        for candidate in candidates:
            if isinstance(
                candidate,
                bool,
            ):
                continue

            if isinstance(
                candidate,
                (int, float),
            ):
                numeric_values.append(
                    float(candidate)
                )
                continue

            if isinstance(
                candidate,
                str,
            ):
                cleaned = "".join(
                    character
                    for character in candidate
                    if (
                        character.isdigit()
                        or character == "."
                    )
                )

                if not cleaned:
                    continue

                try:
                    numeric_values.append(
                        float(cleaned)
                    )
                except ValueError:
                    continue

        if not numeric_values:
            return None

        return min(
            numeric_values
        )

    @staticmethod
    def _extract_departure(
        trip: dict[str, Any],
    ) -> str | None:
        candidates: list[Any] = [
            trip.get("departure_time"),
            trip.get("departure"),
            trip.get("start_time"),
        ]

        timings = trip.get(
            "timings"
        )

        if isinstance(
            timings,
            dict,
        ):
            candidates.extend(
                [
                    timings.get(
                        "departure"
                    ),
                    timings.get(
                        "departure_time"
                    ),
                    timings.get(
                        "start_time"
                    ),
                ]
            )

        for candidate in candidates:
            if candidate:
                return str(candidate)

        return None

    @staticmethod
    def _time_sort_value(
        value: str | None,
    ) -> tuple[int, int]:
        if not value:
            return 99, 99

        normalized = (
            value.strip().lower()
        )

        try:
            if normalized.endswith(
                ("am", "pm")
            ):
                meridiem = normalized[-2:]

                time_part = (
                    normalized[:-2]
                    .strip()
                )

                hour_text, _, minute_text = (
                    time_part.partition(":")
                )

                hour = int(
                    hour_text
                )

                minute = int(
                    minute_text or "0"
                )

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

                return hour, minute

            hour_text, _, minute_text = (
                normalized.partition(":")
            )

            return (
                int(hour_text),
                int(
                    minute_text or "0"
                ),
            )

        except ValueError:
            return 99, 99

    @staticmethod
    def _filter_display_name(
        filter_name: str,
    ) -> str:
        display_names = {
            "maximum_price": "price",
            "minimum_seats": (
                "seat availability"
            ),
            "departure_time": (
                "departure time"
            ),
            "bus_type": "bus type",
            "operator": "operator",
        }

        return display_names.get(
            filter_name,
            filter_name.replace(
                "_",
                " ",
            ),
        )

    @staticmethod
    def _human_join(
        values: list[str],
    ) -> str:
        cleaned = [
            value
            for value in values
            if value
        ]

        if not cleaned:
            return ""

        if len(cleaned) == 1:
            return cleaned[0]

        if len(cleaned) == 2:
            return (
                f"{cleaned[0]} and "
                f"{cleaned[1]}"
            )

        return (
            f"{', '.join(cleaned[:-1])}, "
            f"and {cleaned[-1]}"
        )


chat_response_service = (
    ChatResponseService()
)