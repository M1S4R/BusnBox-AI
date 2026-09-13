from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class InventorySortBy(StrEnum):
    PRICE = "price"
    DEPARTURE_TIME = "departure_time"
    DURATION = "duration"


class InventorySearchRequest(BaseModel):
    source: str = Field(min_length=2, max_length=100)
    destination: str = Field(min_length=2, max_length=100)
    travel_date: date

    minimum_seats: int = Field(default=1, ge=1, le=20)
    bus_type: str | None = None
    operator: str | None = None
    maximum_price: Decimal | None = Field(default=None, ge=0)

    sort_by: InventorySortBy = InventorySortBy.DEPARTURE_TIME
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=50)


class InventoryOperator(BaseModel):
    id: str
    name: str


class InventoryBus(BaseModel):
    id: str
    name: str
    bus_type: str
    registration_number: str | None = None

    amenities: list[str] = Field(default_factory=list)
    total_seats: int | None = Field(default=None, ge=0)


class InventoryTrip(BaseModel):
    id: str

    source: str
    destination: str

    departure_time: datetime
    arrival_time: datetime

    operator: InventoryOperator
    bus: InventoryBus

    price: Decimal = Field(ge=0)
    available_seats: int = Field(ge=0)

    boarding_point: str | None = None
    dropping_point: str | None = None
    booking_url: HttpUrl | None = None


class InventorySearchResult(BaseModel):
    source: str
    destination: str
    travel_date: date
    provider: str

    total_results: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0

    trips: list[InventoryTrip] = Field(default_factory=list)
