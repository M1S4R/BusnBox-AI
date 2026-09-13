from datetime import datetime, time, timedelta
from decimal import Decimal
from math import ceil

from app.integrations.inventory.base import InventoryProvider
from app.schemas.inventory import (
    InventoryBus,
    InventoryOperator,
    InventorySearchRequest,
    InventorySearchResult,
    InventorySortBy,
    InventoryTrip,
)


class MockInventoryProvider(InventoryProvider):
    async def search_trips(
        self,
        search: InventorySearchRequest,
    ) -> InventorySearchResult:
        trips = self._build_mock_trips(search)

        trips = self._apply_filters(
            trips=trips,
            search=search,
        )

        trips = self._sort_trips(
            trips=trips,
            sort_by=search.sort_by,
        )

        total_results = len(trips)
        total_pages = (
            ceil(total_results / search.page_size)
            if total_results > 0
            else 0
        )

        start_index = (search.page - 1) * search.page_size
        end_index = start_index + search.page_size
        paginated_trips = trips[start_index:end_index]

        return InventorySearchResult(
            source=search.source,
            destination=search.destination,
            travel_date=search.travel_date,
            provider="mock",
            total_results=total_results,
            page=search.page,
            page_size=search.page_size,
            total_pages=total_pages,
            trips=paginated_trips,
        )

    def _build_mock_trips(
        self,
        search: InventorySearchRequest,
    ) -> list[InventoryTrip]:
        trip_data = [
            {
                "id": "mock-trip-001",
                "departure": time(5, 30),
                "duration": (6, 15),
                "operator_id": "operator-001",
                "operator": "BusNBox Demo Travels",
                "bus_id": "bus-001",
                "bus_name": "Morning Star",
                "bus_type": "AC Sleeper",
                "registration": "TN-01-BNB-1001",
                "amenities": [
                    "Charging Point",
                    "Blanket",
                    "Water Bottle",
                ],
                "seats": 24,
                "total_seats": 36,
                "price": "649.00",
            },
            {
                "id": "mock-trip-002",
                "departure": time(7, 0),
                "duration": (6, 45),
                "operator_id": "operator-002",
                "operator": "GreenLine Express",
                "bus_id": "bus-002",
                "bus_name": "Green Cruiser",
                "bus_type": "AC Seater",
                "registration": "KA-01-GL-2002",
                "amenities": [
                    "Charging Point",
                    "WiFi",
                ],
                "seats": 18,
                "total_seats": 40,
                "price": "599.00",
            },
            {
                "id": "mock-trip-003",
                "departure": time(8, 30),
                "duration": (7, 0),
                "operator_id": "operator-003",
                "operator": "Southern Roadways",
                "bus_id": "bus-003",
                "bus_name": "Southern Comfort",
                "bus_type": "Non-AC Seater",
                "registration": "TN-22-SR-3003",
                "amenities": [
                    "Water Bottle",
                ],
                "seats": 30,
                "total_seats": 44,
                "price": "499.00",
            },
            {
                "id": "mock-trip-004",
                "departure": time(10, 0),
                "duration": (6, 30),
                "operator_id": "operator-004",
                "operator": "Kaveri Travels",
                "bus_id": "bus-004",
                "bus_name": "Kaveri Premium",
                "bus_type": "AC Sleeper",
                "registration": "KA-05-KV-4004",
                "amenities": [
                    "Charging Point",
                    "Blanket",
                    "WiFi",
                    "Water Bottle",
                ],
                "seats": 8,
                "total_seats": 36,
                "price": "949.00",
            },
            {
                "id": "mock-trip-005",
                "departure": time(12, 15),
                "duration": (6, 50),
                "operator_id": "operator-005",
                "operator": "BusNBox Intercity",
                "bus_id": "bus-005",
                "bus_name": "City Connector",
                "bus_type": "AC Seater",
                "registration": "TN-01-BNB-5005",
                "amenities": [
                    "Charging Point",
                    "Reading Light",
                ],
                "seats": 22,
                "total_seats": 40,
                "price": "699.00",
            },
            {
                "id": "mock-trip-006",
                "departure": time(14, 0),
                "duration": (7, 20),
                "operator_id": "operator-006",
                "operator": "Royal Wheels",
                "bus_id": "bus-006",
                "bus_name": "Royal Executive",
                "bus_type": "Volvo Multi-Axle",
                "registration": "KA-03-RW-6006",
                "amenities": [
                    "Charging Point",
                    "WiFi",
                    "Blanket",
                    "Snacks",
                ],
                "seats": 14,
                "total_seats": 42,
                "price": "1199.00",
            },
            {
                "id": "mock-trip-007",
                "departure": time(16, 30),
                "duration": (6, 10),
                "operator_id": "operator-007",
                "operator": "Metro Link Travels",
                "bus_id": "bus-007",
                "bus_name": "Metro Rider",
                "bus_type": "Non-AC Seater",
                "registration": "TN-09-ML-7007",
                "amenities": [
                    "Water Bottle",
                    "Reading Light",
                ],
                "seats": 27,
                "total_seats": 45,
                "price": "549.00",
            },
            {
                "id": "mock-trip-008",
                "departure": time(18, 0),
                "duration": (6, 40),
                "operator_id": "operator-008",
                "operator": "BlueBird Coaches",
                "bus_id": "bus-008",
                "bus_name": "BlueBird Deluxe",
                "bus_type": "AC Sleeper",
                "registration": "KA-04-BB-8008",
                "amenities": [
                    "Charging Point",
                    "Blanket",
                    "Water Bottle",
                ],
                "seats": 16,
                "total_seats": 36,
                "price": "849.00",
            },
            {
                "id": "mock-trip-009",
                "departure": time(19, 15),
                "duration": (6, 5),
                "operator_id": "operator-009",
                "operator": "BusNBox Night Express",
                "bus_id": "bus-009",
                "bus_name": "Night Falcon",
                "bus_type": "AC Sleeper",
                "registration": "TN-01-BNB-9009",
                "amenities": [
                    "Charging Point",
                    "Blanket",
                    "WiFi",
                    "Water Bottle",
                ],
                "seats": 21,
                "total_seats": 36,
                "price": "899.00",
            },
            {
                "id": "mock-trip-010",
                "departure": time(20, 30),
                "duration": (7, 10),
                "operator_id": "operator-010",
                "operator": "Orange Tours",
                "bus_id": "bus-010",
                "bus_name": "Orange Dream",
                "bus_type": "Volvo Multi-Axle",
                "registration": "KA-02-OT-1010",
                "amenities": [
                    "Charging Point",
                    "WiFi",
                    "Blanket",
                    "Snacks",
                    "Water Bottle",
                ],
                "seats": 6,
                "total_seats": 42,
                "price": "1299.00",
            },
            {
                "id": "mock-trip-011",
                "departure": time(21, 30),
                "duration": (6, 30),
                "operator_id": "operator-011",
                "operator": "CityLine Transport",
                "bus_id": "bus-011",
                "bus_name": "Night Rider",
                "bus_type": "AC Sleeper",
                "registration": "TN-11-CL-1111",
                "amenities": [
                    "Charging Point",
                    "Blanket",
                    "Water Bottle",
                ],
                "seats": 12,
                "total_seats": 36,
                "price": "799.00",
            },
            {
                "id": "mock-trip-012",
                "departure": time(23, 0),
                "duration": (6, 55),
                "operator_id": "operator-012",
                "operator": "National Express",
                "bus_id": "bus-012",
                "bus_name": "Midnight Express",
                "bus_type": "AC Seater",
                "registration": "KA-01-NE-1212",
                "amenities": [
                    "Charging Point",
                    "Water Bottle",
                    "Reading Light",
                ],
                "seats": 25,
                "total_seats": 40,
                "price": "679.00",
            },
        ]

        trips: list[InventoryTrip] = []

        for item in trip_data:
            departure = datetime.combine(
                search.travel_date,
                item["departure"],
            )

            duration_hours, duration_minutes = item["duration"]

            arrival = departure + timedelta(
                hours=duration_hours,
                minutes=duration_minutes,
            )

            trips.append(
                InventoryTrip(
                    id=item["id"],
                    source=search.source,
                    destination=search.destination,
                    departure_time=departure,
                    arrival_time=arrival,
                    operator=InventoryOperator(
                        id=item["operator_id"],
                        name=item["operator"],
                    ),
                    bus=InventoryBus(
                        id=item["bus_id"],
                        name=item["bus_name"],
                        bus_type=item["bus_type"],
                        registration_number=item["registration"],
                        amenities=item["amenities"],
                        total_seats=item["total_seats"],
                    ),
                    price=Decimal(item["price"]),
                    available_seats=item["seats"],
                    boarding_point=search.source,
                    dropping_point=search.destination,
                    booking_url=None,
                )
            )

        return trips

    def _apply_filters(
        self,
        trips: list[InventoryTrip],
        search: InventorySearchRequest,
    ) -> list[InventoryTrip]:
        filtered_trips = trips

        filtered_trips = [
            trip
            for trip in filtered_trips
            if trip.available_seats >= search.minimum_seats
        ]

        if search.bus_type:
            requested_bus_type = (
                search.bus_type
                .casefold()
                .strip()
            )

            filtered_trips = [
                trip
                for trip in filtered_trips
                if self._matches_bus_type(
                    actual=trip.bus.bus_type,
                    requested=requested_bus_type,
                )
            ]

        if search.operator:
            requested_operator = search.operator.casefold().strip()

            filtered_trips = [
                trip
                for trip in filtered_trips
                if requested_operator
                in trip.operator.name.casefold()
            ]

        if search.maximum_price is not None:
            filtered_trips = [
                trip
                for trip in filtered_trips
                if trip.price <= search.maximum_price
            ]

        return filtered_trips

    @staticmethod
    def _matches_bus_type(
        actual: str,
        requested: str,
    ) -> bool:
        normalized_actual = (
            actual
            .casefold()
            .strip()
            .replace("_", " ")
        )

        normalized_requested = (
            requested
            .casefold()
            .strip()
            .replace("_", " ")
        )

        compact_actual = (
            normalized_actual
            .replace("-", " ")
        )

        compact_requested = (
            normalized_requested
            .replace("-", " ")
        )

        actual_tokens = set(
            compact_actual.split()
        )

        requested_tokens = set(
            compact_requested.split()
        )

        is_non_ac_actual = (
            "non ac" in compact_actual
            or (
                "non" in actual_tokens
                and "ac" in actual_tokens
            )
        )

        is_ac_actual = (
            "ac" in actual_tokens
            and not is_non_ac_actual
        )

        if compact_requested == "ac":
            return is_ac_actual

        if compact_requested == "non ac":
            return is_non_ac_actual

        if compact_requested == "sleeper":
            return "sleeper" in actual_tokens

        if compact_requested == "seater":
            return "seater" in actual_tokens

        if compact_requested == "volvo":
            return "volvo" in actual_tokens

        if compact_requested in {
            "ac sleeper",
            "sleeper ac",
        }:
            return (
                is_ac_actual
                and "sleeper" in actual_tokens
            )

        if compact_requested in {
            "ac seater",
            "seater ac",
        }:
            return (
                is_ac_actual
                and "seater" in actual_tokens
            )

        if compact_requested in {
            "non ac sleeper",
            "sleeper non ac",
        }:
            return (
                is_non_ac_actual
                and "sleeper" in actual_tokens
            )

        if compact_requested in {
            "non ac seater",
            "seater non ac",
        }:
            return (
                is_non_ac_actual
                and "seater" in actual_tokens
            )

        return requested_tokens.issubset(
            actual_tokens
        )

    def _sort_trips(
        self,
        trips: list[InventoryTrip],
        sort_by: InventorySortBy,
    ) -> list[InventoryTrip]:
        if sort_by == InventorySortBy.PRICE:
            return sorted(
                trips,
                key=lambda trip: trip.price,
            )

        if sort_by == InventorySortBy.DURATION:
            return sorted(
                trips,
                key=lambda trip: (
                    trip.arrival_time - trip.departure_time
                ),
            )

        return sorted(
            trips,
            key=lambda trip: trip.departure_time,
        )