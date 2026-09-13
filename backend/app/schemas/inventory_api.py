from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.inventory import InventorySortBy, InventoryTrip


class InventorySearchBody(BaseModel):
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


class InventorySearchResponse(BaseModel):
    success: bool = True
    source: str
    destination: str
    travel_date: date
    provider: str

    trip_count: int
    total_results: int
    page: int
    page_size: int
    total_pages: int

    trips: list[InventoryTrip] = Field(default_factory=list)


class InventoryErrorResponse(BaseModel):
    success: bool = False
    detail: str
