from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

IntentName = Literal[
    "search_trip",
    "greeting",
    "help",
    "unknown",
]


class TripSearchParameters(BaseModel):
    source: str | None = None
    destination: str | None = None
    travel_date: date | None = None
    bus_type: str | None = None
    max_fare: Decimal | None = Field(default=None, ge=0)


class IntentExtractionResult(BaseModel):
    intent: IntentName
    parameters: TripSearchParameters = Field(
        default_factory=TripSearchParameters
    )
    missing_fields: list[str] = Field(default_factory=list)