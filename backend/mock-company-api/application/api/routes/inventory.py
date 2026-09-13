from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from application.database.session import get_database_session
from application.schemas.inventory import (
    InventorySearchRequest,
    InventorySearchResponse,
    InventoryTrip,
)
from application.services.inventory_service import InventoryService

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


def _map_trips_to_response(trips) -> InventorySearchResponse:
    response_trips = [
        InventoryTrip(
            trip_id=trip.id,
            operator=trip.bus.operator.name,
            bus_number=trip.bus.bus_number,
            bus_type=trip.bus.bus_type,
            source=trip.route.source_city.name,
            destination=trip.route.destination_city.name,
            departure_time=trip.departure_time,
            arrival_time=trip.arrival_time,
            fare=trip.price,
            available_seats=trip.available_seats,
        )
        for trip in trips
    ]

    return InventorySearchResponse(
        success=True,
        count=len(response_trips),
        trips=response_trips,
    )


@router.post("/search", response_model=InventorySearchResponse)
async def search_inventory(
    payload: InventorySearchRequest,
    session: AsyncSession = Depends(get_database_session),
) -> InventorySearchResponse:
    service = InventoryService(session)

    trips = await service.search_trips(
        source=payload.source,
        destination=payload.destination,
        travel_date=payload.travel_date,
    )

    return _map_trips_to_response(trips)


@router.get("/search", response_model=InventorySearchResponse)
async def search_inventory_get(
    source: str = Query(..., description="Source city"),
    destination: str = Query(..., description="Destination city"),
    travel_date: date = Query(..., description="Travel date YYYY-MM-DD"),
    session: AsyncSession = Depends(get_database_session),
) -> InventorySearchResponse:
    service = InventoryService(session)

    trips = await service.search_trips(
        source=source,
        destination=destination,
        travel_date=travel_date,
    )

    return _map_trips_to_response(trips)