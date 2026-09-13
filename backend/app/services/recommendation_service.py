from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TripRecommendation:
    """
    A structured recommendation generated from validated
    inventory data.
    """

    id: str
    type: str
    trip_id: str | None
    title: str
    reason: str
    operator: str | None

    def model_dump(self) -> dict[str, str | None]:
        return {
            "id": self.id,
            "type": self.type,
            "trip_id": self.trip_id,
            "title": self.title,
            "reason": self.reason,
            "operator": self.operator,
        }


class RecommendationService:
    """
    Generates grounded bus recommendations using deterministic
    rules over validated inventory results.

    The service never calls Ollama and never invents trip data.
    """

    MAX_RECOMMENDATIONS = 4

    def build_recommendations(
        self,
        *,
        trips: list[dict[str, Any]],
    ) -> list[TripRecommendation]:
        if not trips:
            return []

        recommendations: list[TripRecommendation] = []

        cheapest = self._find_cheapest_trip(trips)

        if cheapest is not None:
            recommendations.append(
                self._build_cheapest_recommendation(
                    cheapest
                )
            )

        earliest = self._find_earliest_trip(trips)

        if earliest is not None:
            recommendations.append(
                self._build_earliest_recommendation(
                    earliest
                )
            )

        best_rated = self._find_best_rated_trip(
            trips
        )

        if best_rated is not None:
            recommendations.append(
                self._build_best_rated_recommendation(
                    best_rated
                )
            )

        most_seats = self._find_most_seats_trip(
            trips
        )

        if most_seats is not None:
            recommendations.append(
                self._build_most_seats_recommendation(
                    most_seats
                )
            )

        best_value = self._find_best_value_trip(
            trips=trips,
            cheapest_trip=cheapest,
        )

        if best_value is not None:
            recommendations.insert(
                0,
                self._build_best_value_recommendation(
                    trip=best_value,
                    cheapest_trip=cheapest,
                ),
            )

        return self._unique_and_limit(
            recommendations
        )

    def _build_cheapest_recommendation(
        self,
        trip: dict[str, Any],
    ) -> TripRecommendation:
        price = self._extract_price(trip)
        operator = self._extract_operator(trip)

        if price is not None:
            reason = (
                f"{operator or 'This bus'} has the lowest "
                f"available fare at {self._format_price(price)}."
            )
        else:
            reason = (
                f"{operator or 'This bus'} has the lowest "
                "available fare."
            )

        return TripRecommendation(
            id=self._recommendation_id(
                "cheapest",
                trip,
            ),
            type="cheapest",
            trip_id=self._extract_trip_id(trip),
            title="Cheapest option",
            reason=reason,
            operator=operator,
        )

    def _build_earliest_recommendation(
        self,
        trip: dict[str, Any],
    ) -> TripRecommendation:
        departure = self._extract_departure_text(
            trip
        )
        operator = self._extract_operator(trip)

        if departure:
            reason = (
                f"{operator or 'This bus'} has the earliest "
                f"departure at {departure}."
            )
        else:
            reason = (
                f"{operator or 'This bus'} has the earliest "
                "available departure."
            )

        return TripRecommendation(
            id=self._recommendation_id(
                "earliest",
                trip,
            ),
            type="earliest",
            trip_id=self._extract_trip_id(trip),
            title="Earliest departure",
            reason=reason,
            operator=operator,
        )

    def _build_best_rated_recommendation(
        self,
        trip: dict[str, Any],
    ) -> TripRecommendation:
        rating = self._extract_rating(trip)
        operator = self._extract_operator(trip)

        if rating is not None:
            reason = (
                f"{operator or 'This bus'} has the highest "
                f"available rating at {rating:.1f}."
            )
        else:
            reason = (
                f"{operator or 'This bus'} has the highest "
                "available rating."
            )

        return TripRecommendation(
            id=self._recommendation_id(
                "best-rated",
                trip,
            ),
            type="best_rated",
            trip_id=self._extract_trip_id(trip),
            title="Best rated",
            reason=reason,
            operator=operator,
        )

    def _build_most_seats_recommendation(
        self,
        trip: dict[str, Any],
    ) -> TripRecommendation:
        seats = self._extract_available_seats(
            trip
        )
        operator = self._extract_operator(trip)

        if seats is not None:
            reason = (
                f"{operator or 'This bus'} has the most "
                f"availability with {seats} seats left."
            )
        else:
            reason = (
                f"{operator or 'This bus'} has the most "
                "available seats."
            )

        return TripRecommendation(
            id=self._recommendation_id(
                "most-seats",
                trip,
            ),
            type="most_seats",
            trip_id=self._extract_trip_id(trip),
            title="Most seats available",
            reason=reason,
            operator=operator,
        )

    def _build_best_value_recommendation(
        self,
        *,
        trip: dict[str, Any],
        cheapest_trip: dict[str, Any] | None,
    ) -> TripRecommendation:
        operator = self._extract_operator(trip)
        price = self._extract_price(trip)
        rating = self._extract_rating(trip)
        seats = self._extract_available_seats(
            trip
        )

        reason_parts: list[str] = []

        cheapest_price = (
            self._extract_price(cheapest_trip)
            if cheapest_trip is not None
            else None
        )

        if (
            price is not None
            and cheapest_price is not None
        ):
            difference = price - cheapest_price

            if difference <= 0:
                reason_parts.append(
                    "it matches the lowest fare"
                )
            else:
                reason_parts.append(
                    "it costs only "
                    f"{self._format_price(difference)} "
                    "more than the cheapest option"
                )

        if rating is not None:
            reason_parts.append(
                f"has a {rating:.1f} rating"
            )

        if seats is not None:
            reason_parts.append(
                f"has {seats} seats available"
            )

        bus_type = self._extract_bus_type(trip)

        if bus_type:
            reason_parts.append(
                f"is a {bus_type} bus"
            )

        if reason_parts:
            joined_reason = self._join_reason_parts(
                reason_parts
            )

            reason = (
                f"{operator or 'This bus'} offers strong "
                f"overall value because {joined_reason}."
            )
        else:
            reason = (
                f"{operator or 'This bus'} offers a good "
                "balance of fare and available features."
            )

        return TripRecommendation(
            id=self._recommendation_id(
                "best-value",
                trip,
            ),
            type="best_value",
            trip_id=self._extract_trip_id(trip),
            title="Best value",
            reason=reason,
            operator=operator,
        )

    def _find_cheapest_trip(
        self,
        trips: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        candidates = [
            trip
            for trip in trips
            if self._extract_price(trip) is not None
        ]

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda trip: (
                self._extract_price(trip)
                or float("inf")
            ),
        )

    def _find_earliest_trip(
        self,
        trips: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        candidates: list[
            tuple[int, dict[str, Any]]
        ] = []

        for trip in trips:
            minutes = self._extract_departure_minutes(
                trip
            )

            if minutes is not None:
                candidates.append(
                    (minutes, trip)
                )

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda item: item[0],
        )[1]

    def _find_best_rated_trip(
        self,
        trips: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        candidates = [
            trip
            for trip in trips
            if self._extract_rating(trip) is not None
        ]

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda trip: (
                self._extract_rating(trip)
                or 0.0
            ),
        )

    def _find_most_seats_trip(
        self,
        trips: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        candidates = [
            trip
            for trip in trips
            if (
                self._extract_available_seats(
                    trip
                )
                is not None
            )
        ]

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda trip: (
                self._extract_available_seats(
                    trip
                )
                or 0
            ),
        )

    def _find_best_value_trip(
        self,
        *,
        trips: list[dict[str, Any]],
        cheapest_trip: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        priced_trips = [
            trip
            for trip in trips
            if self._extract_price(trip) is not None
        ]

        if not priced_trips:
            return None

        prices = [
            self._extract_price(trip)
            for trip in priced_trips
        ]

        valid_prices = [
            price
            for price in prices
            if price is not None
        ]

        if not valid_prices:
            return None

        minimum_price = min(valid_prices)
        maximum_price = max(valid_prices)
        price_range = maximum_price - minimum_price

        scored_candidates: list[
            tuple[float, dict[str, Any]]
        ] = []

        for trip in priced_trips:
            price = self._extract_price(trip)

            if price is None:
                continue

            if price_range > 0:
                price_score = (
                    maximum_price - price
                ) / price_range
            else:
                price_score = 1.0

            rating = self._extract_rating(trip)

            rating_score = (
                min(max(rating / 5.0, 0.0), 1.0)
                if rating is not None
                else 0.5
            )

            seats = self._extract_available_seats(
                trip
            )

            seats_score = (
                min(seats / 40.0, 1.0)
                if seats is not None
                else 0.5
            )

            bus_type = (
                self._extract_bus_type(trip)
                or ""
            ).casefold()

            comfort_score = 0.0

            if "ac" in bus_type:
                comfort_score += 0.5

            if "sleeper" in bus_type:
                comfort_score += 0.5

            total_score = (
                price_score * 0.50
                + rating_score * 0.25
                + seats_score * 0.15
                + comfort_score * 0.10
            )

            scored_candidates.append(
                (total_score, trip)
            )

        if not scored_candidates:
            return cheapest_trip

        return max(
            scored_candidates,
            key=lambda item: item[0],
        )[1]

    @staticmethod
    def _extract_trip_id(
        trip: dict[str, Any],
    ) -> str | None:
        candidates = [
            trip.get("trip_id"),
            trip.get("id"),
            trip.get("inventory_id"),
            trip.get("service_id"),
            trip.get("bus_id"),
        ]

        for candidate in candidates:
            if candidate is None:
                continue

            value = str(candidate).strip()

            if value:
                return value

        return None

    @staticmethod
    def _extract_operator(
        trip: dict[str, Any],
    ) -> str | None:
        candidates = [
            trip.get("operator"),
            trip.get("operator_name"),
            trip.get("travels"),
            trip.get("provider"),
        ]

        for candidate in candidates:
            if isinstance(candidate, dict):
                candidate = (
                    candidate.get("name")
                    or candidate.get("operator_name")
                )

            if candidate is None:
                continue

            value = str(candidate).strip()

            if value:
                return value

        return None

    @classmethod
    def _extract_price(
        cls,
        trip: dict[str, Any] | None,
    ) -> float | None:
        if trip is None:
            return None

        candidates: list[Any] = [
            trip.get("price"),
            trip.get("fare"),
            trip.get("starting_price"),
            trip.get("minimum_price"),
            trip.get("base_fare"),
        ]

        fares = trip.get("fares")

        if isinstance(fares, dict):
            candidates.extend(
                fares.values()
            )

        elif isinstance(fares, list):
            candidates.extend(fares)

        parsed_prices = [
            parsed
            for candidate in candidates
            if (
                parsed := cls._parse_number(
                    candidate
                )
            )
            is not None
        ]

        if not parsed_prices:
            return None

        return min(parsed_prices)

    @classmethod
    def _extract_rating(
        cls,
        trip: dict[str, Any],
    ) -> float | None:
        candidates = [
            trip.get("rating"),
            trip.get("operator_rating"),
            trip.get("average_rating"),
            trip.get("score"),
        ]

        for candidate in candidates:
            parsed = cls._parse_number(
                candidate
            )

            if parsed is None:
                continue

            if 0 <= parsed <= 5:
                return parsed

            if 0 <= parsed <= 10:
                return parsed / 2

        return None

    @classmethod
    def _extract_available_seats(
        cls,
        trip: dict[str, Any],
    ) -> int | None:
        candidates = [
            trip.get("available_seats"),
            trip.get("seats_available"),
            trip.get("seat_count"),
            trip.get("remaining_seats"),
            trip.get("seats"),
        ]

        for candidate in candidates:
            if isinstance(candidate, list):
                return len(candidate)

            if isinstance(candidate, dict):
                nested_value = (
                    candidate.get("available")
                    or candidate.get(
                        "available_seats"
                    )
                    or candidate.get("count")
                )

                parsed = cls._parse_number(
                    nested_value
                )
            else:
                parsed = cls._parse_number(
                    candidate
                )

            if parsed is not None and parsed >= 0:
                return int(parsed)

        return None

    @staticmethod
    def _extract_bus_type(
        trip: dict[str, Any],
    ) -> str | None:
        candidates = [
            trip.get("bus_type"),
            trip.get("vehicle_type"),
            trip.get("coach_type"),
            trip.get("type"),
        ]

        for candidate in candidates:
            if candidate is None:
                continue

            value = str(candidate).strip()

            if value:
                return value

        return None

    @classmethod
    def _extract_departure_text(
        cls,
        trip: dict[str, Any],
    ) -> str | None:
        candidates = [
            trip.get("departure_time"),
            trip.get("departure"),
            trip.get("start_time"),
            trip.get("boarding_time"),
        ]

        timings = trip.get("timings")

        if isinstance(timings, dict):
            candidates.extend(
                [
                    timings.get("departure"),
                    timings.get(
                        "departure_time"
                    ),
                    timings.get("start_time"),
                ]
            )

        for candidate in candidates:
            if candidate is None:
                continue

            value = str(candidate).strip()

            if value:
                return value

        return None

    @classmethod
    def _extract_departure_minutes(
        cls,
        trip: dict[str, Any],
    ) -> int | None:
        value = cls._extract_departure_text(
            trip
        )

        if not value:
            return None

        formats = (
            "%H:%M",
            "%H:%M:%S",
            "%I:%M %p",
            "%I:%M%p",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        )

        cleaned = value.strip()

        for time_format in formats:
            try:
                parsed = datetime.strptime(
                    cleaned,
                    time_format,
                )

                return (
                    parsed.hour * 60
                    + parsed.minute
                )

            except ValueError:
                continue

        if "T" in cleaned:
            try:
                parsed_iso = (
                    datetime.fromisoformat(
                        cleaned.replace(
                            "Z",
                            "+00:00",
                        )
                    )
                )

                return (
                    parsed_iso.hour * 60
                    + parsed_iso.minute
                )

            except ValueError:
                return None

        return None

    @staticmethod
    def _parse_number(
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
            if (
                character.isdigit()
                or character in {".", "-"}
            )
        )

        if not cleaned:
            return None

        try:
            return float(cleaned)

        except ValueError:
            return None

    @staticmethod
    def _format_price(
        value: float,
    ) -> str:
        if value.is_integer():
            return f"₹{int(value)}"

        return f"₹{value:.2f}"

    @staticmethod
    def _join_reason_parts(
        parts: list[str],
    ) -> str:
        if len(parts) == 1:
            return parts[0]

        if len(parts) == 2:
            return (
                f"{parts[0]} and {parts[1]}"
            )

        return (
            ", ".join(parts[:-1])
            + f", and {parts[-1]}"
        )

    @classmethod
    def _recommendation_id(
        cls,
        recommendation_type: str,
        trip: dict[str, Any],
    ) -> str:
        trip_id = cls._extract_trip_id(trip)

        if trip_id:
            normalized_trip_id = (
                trip_id
                .strip()
                .lower()
                .replace(" ", "-")
            )

            return (
                f"{recommendation_type}-"
                f"{normalized_trip_id}"
            )

        operator = (
            cls._extract_operator(trip)
            or "trip"
        )

        normalized_operator = (
            operator
            .strip()
            .lower()
            .replace(" ", "-")
        )

        return (
            f"{recommendation_type}-"
            f"{normalized_operator}"
        )

    def _unique_and_limit(
        self,
        recommendations: list[
            TripRecommendation
        ],
    ) -> list[TripRecommendation]:
        unique: list[TripRecommendation] = []
        seen_types: set[str] = set()
        seen_pairs: set[
            tuple[str, str | None]
        ] = set()

        for recommendation in recommendations:
            pair = (
                recommendation.type,
                recommendation.trip_id,
            )

            if recommendation.type in seen_types:
                continue

            if pair in seen_pairs:
                continue

            seen_types.add(
                recommendation.type
            )
            seen_pairs.add(pair)
            unique.append(recommendation)

            if (
                len(unique)
                >= self.MAX_RECOMMENDATIONS
            ):
                break

        return unique


recommendation_service = RecommendationService()
