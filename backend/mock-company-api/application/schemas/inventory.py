from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class InventorySearchRequest(BaseModel):
    source: str = Field(min_length=2, max_length=100)
    destination: str = Field(min_length=2, max_length=100)
    travel_date: date


class InventoryTrip(BaseModel):
    trip_id: int
    operator: str
    bus_number: str
    bus_type: str
    source: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    fare: Decimal
    available_seats: int


class InventorySearchResponse(BaseModel):
    success: bool
    count: int
    trips: list[InventoryTrip]