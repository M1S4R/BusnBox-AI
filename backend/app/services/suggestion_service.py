from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.schemas.chat import ChatParameters


@dataclass(frozen=True)
class ChatSuggestion:
    """
    A structured suggestion that can be rendered as a clickable
    chip by the frontend.
    """

    id: str
    label: str
    message: str
    action: str

    def model_dump(self) -> dict[str, str]:
        return {
            "id": self.id,
            "label": self.label,
            "message": self.message,
            "action": self.action,
        }


class SuggestionService:
    """
    Generates deterministic next-action suggestions from the
    current search parameters and validated inventory results.

    The service never invents trip information and does not call
    Ollama.
    """

    MAX_SUGGESTIONS = 5

    def build_search_suggestions(
        self,
        *,
        parameters: ChatParameters,
        trips: list[dict[str, Any]],
    ) -> list[ChatSuggestion]:
        filters = dict(parameters.filters or {})

        if not trips:
            return self._build_no_result_suggestions(
                parameters=parameters,
            )

        suggestions: list[ChatSuggestion] = []

        self._add_bus_type_suggestions(
            suggestions=suggestions,
            filters=filters,
        )

        self._add_price_suggestions(
            suggestions=suggestions,
            filters=filters,
            trips=trips,
        )

        self._add_time_suggestions(
            suggestions=suggestions,
            filters=filters,
        )

        self._add_sorting_suggestions(
            suggestions=suggestions,
        )

        self._add_filter_management_suggestions(
            suggestions=suggestions,
            filters=filters,
        )

        return self._unique_and_limit(suggestions)

    def build_missing_parameter_suggestions(
        self,
        *,
        missing_parameter: str,
    ) -> list[ChatSuggestion]:
        if missing_parameter == "source":
            return [
                ChatSuggestion(
                    id="source-chennai",
                    label="From Chennai",
                    message="I am travelling from Chennai",
                    action="set_source",
                ),
                ChatSuggestion(
                    id="source-bangalore",
                    label="From Bangalore",
                    message="I am travelling from Bangalore",
                    action="set_source",
                ),
                ChatSuggestion(
                    id="source-coimbatore",
                    label="From Coimbatore",
                    message="I am travelling from Coimbatore",
                    action="set_source",
                ),
            ]

        if missing_parameter == "destination":
            return [
                ChatSuggestion(
                    id="destination-bangalore",
                    label="To Bangalore",
                    message="I want to travel to Bangalore",
                    action="set_destination",
                ),
                ChatSuggestion(
                    id="destination-chennai",
                    label="To Chennai",
                    message="I want to travel to Chennai",
                    action="set_destination",
                ),
                ChatSuggestion(
                    id="destination-hyderabad",
                    label="To Hyderabad",
                    message="I want to travel to Hyderabad",
                    action="set_destination",
                ),
            ]

        if missing_parameter == "travel_date":
            return [
                ChatSuggestion(
                    id="date-today",
                    label="Today",
                    message="Travel today",
                    action="set_travel_date",
                ),
                ChatSuggestion(
                    id="date-tomorrow",
                    label="Tomorrow",
                    message="Travel tomorrow",
                    action="set_travel_date",
                ),
                ChatSuggestion(
                    id="date-next-saturday",
                    label="Next Saturday",
                    message="Travel next Saturday",
                    action="set_travel_date",
                ),
            ]

        return []

    def _build_no_result_suggestions(
        self,
        *,
        parameters: ChatParameters,
    ) -> list[ChatSuggestion]:
        filters = dict(parameters.filters or {})
        suggestions: list[ChatSuggestion] = []

        if "maximum_price" in filters:
            suggestions.append(
                ChatSuggestion(
                    id="remove-price-filter",
                    label="Remove price limit",
                    message="Remove the price filter",
                    action="remove_filter",
                )
            )

            suggestions.append(
                ChatSuggestion(
                    id="increase-budget",
                    label="Increase budget",
                    message="Increase my budget",
                    action="update_filter",
                )
            )

        if "bus_type" in filters:
            suggestions.append(
                ChatSuggestion(
                    id="remove-bus-type-filter",
                    label="Any bus type",
                    message="Remove the bus type filter",
                    action="remove_filter",
                )
            )

        if "operator" in filters:
            suggestions.append(
                ChatSuggestion(
                    id="remove-operator-filter",
                    label="Any operator",
                    message="Remove the operator filter",
                    action="remove_filter",
                )
            )

        if "departure_time" in filters:
            suggestions.append(
                ChatSuggestion(
                    id="remove-time-filter",
                    label="Any departure time",
                    message="Remove the departure time filter",
                    action="remove_filter",
                )
            )

        if filters:
            suggestions.append(
                ChatSuggestion(
                    id="clear-all-filters",
                    label="Clear all filters",
                    message="Remove all filters",
                    action="clear_filters",
                )
            )

        suggestions.extend(
            [
                ChatSuggestion(
                    id="try-tomorrow",
                    label="Try tomorrow",
                    message="Search for tomorrow instead",
                    action="change_date",
                ),
                ChatSuggestion(
                    id="new-route",
                    label="Change route",
                    message="I want to search another route",
                    action="new_search",
                ),
            ]
        )

        return self._unique_and_limit(suggestions)

    @staticmethod
    def _add_bus_type_suggestions(
        *,
        suggestions: list[ChatSuggestion],
        filters: dict[str, Any],
    ) -> None:
        bus_type = str(
            filters.get("bus_type") or ""
        ).casefold()

        if not bus_type:
            suggestions.extend(
                [
                    ChatSuggestion(
                        id="only-ac",
                        label="Only AC",
                        message="Show only AC buses",
                        action="apply_filter",
                    ),
                    ChatSuggestion(
                        id="only-sleeper",
                        label="Only sleeper",
                        message="Show only sleeper buses",
                        action="apply_filter",
                    ),
                ]
            )
            return

        if "ac" not in bus_type:
            suggestions.append(
                ChatSuggestion(
                    id="only-ac",
                    label="Only AC",
                    message="Show only AC buses",
                    action="apply_filter",
                )
            )

        if "sleeper" not in bus_type:
            suggestions.append(
                ChatSuggestion(
                    id="only-sleeper",
                    label="Only sleeper",
                    message="Show only sleeper buses",
                    action="apply_filter",
                )
            )

    def _add_price_suggestions(
        self,
        *,
        suggestions: list[ChatSuggestion],
        filters: dict[str, Any],
        trips: list[dict[str, Any]],
    ) -> None:
        maximum_price = filters.get("maximum_price")

        if maximum_price is not None:
            suggestions.append(
                ChatSuggestion(
                    id="remove-price-filter",
                    label="Remove price limit",
                    message="Remove the price filter",
                    action="remove_filter",
                )
            )
            return

        lowest_price = self._lowest_trip_price(trips)

        if lowest_price is None:
            suggestions.append(
                ChatSuggestion(
                    id="under-1500",
                    label="Under ₹1500",
                    message="Show buses under 1500",
                    action="apply_filter",
                )
            )
            return

        rounded_budget = self._suggested_budget(
            lowest_price
        )

        suggestions.append(
            ChatSuggestion(
                id=f"under-{rounded_budget}",
                label=f"Under ₹{rounded_budget}",
                message=(
                    f"Show buses under {rounded_budget}"
                ),
                action="apply_filter",
            )
        )

    @staticmethod
    def _add_time_suggestions(
        *,
        suggestions: list[ChatSuggestion],
        filters: dict[str, Any],
    ) -> None:
        if "departure_time" in filters:
            suggestions.append(
                ChatSuggestion(
                    id="remove-time-filter",
                    label="Any departure time",
                    message="Remove the departure time filter",
                    action="remove_filter",
                )
            )
            return

        suggestions.append(
            ChatSuggestion(
                id="evening-buses",
                label="Evening buses",
                message="Show evening buses",
                action="apply_filter",
            )
        )

    @staticmethod
    def _add_sorting_suggestions(
        *,
        suggestions: list[ChatSuggestion],
    ) -> None:
        suggestions.extend(
            [
                ChatSuggestion(
                    id="cheapest-first",
                    label="Cheapest first",
                    message="Sort by cheapest",
                    action="sort",
                ),
                ChatSuggestion(
                    id="earliest-first",
                    label="Earliest first",
                    message="Show earliest departures first",
                    action="sort",
                ),
            ]
        )

    @staticmethod
    def _add_filter_management_suggestions(
        *,
        suggestions: list[ChatSuggestion],
        filters: dict[str, Any],
    ) -> None:
        if not filters:
            return

        suggestions.append(
            ChatSuggestion(
                id="clear-all-filters",
                label="Clear filters",
                message="Remove all filters",
                action="clear_filters",
            )
        )

    @staticmethod
    def _lowest_trip_price(
        trips: list[dict[str, Any]],
    ) -> float | None:
        prices: list[float] = []

        for trip in trips:
            candidates: list[Any] = [
                trip.get("price"),
                trip.get("fare"),
                trip.get("starting_price"),
                trip.get("minimum_price"),
            ]

            fares = trip.get("fares")

            if isinstance(fares, dict):
                candidates.extend(fares.values())

            elif isinstance(fares, list):
                candidates.extend(fares)

            for candidate in candidates:
                parsed = SuggestionService._parse_price(
                    candidate
                )

                if parsed is not None:
                    prices.append(parsed)

        if not prices:
            return None

        return min(prices)

    @staticmethod
    def _parse_price(
        value: Any,
    ) -> float | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if not isinstance(value, str):
            return None

        cleaned = "".join(
            character
            for character in value
            if character.isdigit() or character == "."
        )

        if not cleaned:
            return None

        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _suggested_budget(
        lowest_price: float,
    ) -> int:
        target = lowest_price + 300

        rounded = int(
            (target + 99) // 100 * 100
        )

        return max(rounded, 500)

    def _unique_and_limit(
        self,
        suggestions: list[ChatSuggestion],
    ) -> list[ChatSuggestion]:
        unique: list[ChatSuggestion] = []
        seen_ids: set[str] = set()

        for suggestion in suggestions:
            if suggestion.id in seen_ids:
                continue

            seen_ids.add(suggestion.id)
            unique.append(suggestion)

            if len(unique) >= self.MAX_SUGGESTIONS:
                break

        return unique


suggestion_service = SuggestionService()
