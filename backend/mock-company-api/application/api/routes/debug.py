from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from application.database.session import get_database_session
from application.repositories.trip import trip_repository


router = APIRouter(
    prefix="/api/v1/debug",
    tags=["Debug"],
)


@router.get("/trips")
async def get_debug_trips(
    limit: int = Query(default=5, ge=1, le=20),
    session: AsyncSession = Depends(get_database_session),
) -> dict[str, object]:
    try:
        trips = await trip_repository.get_debug_trips(
            session=session,
            limit=limit,
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Database query failed. Check that the ORM models "
                "match the MariaDB table schema."
            ),
        ) from exc

    return {
        "success": True,
        "count": len(trips),
        "trips": [
            {
                "id": trip.id,
                "source": trip.route.source_city.name,
                "destination": trip.route.destination_city.name,
                "departure_time": trip.departure_time,
                "arrival_time": trip.arrival_time,
                "price": str(trip.price),
                "available_seats": trip.available_seats,
                "status": trip.status,
                "operator": {
                    "id": trip.bus.operator.id,
                    "name": trip.bus.operator.name,
                },
                "bus": {
                    "id": trip.bus.id,
                    "name": trip.bus.bus_name,
                    "registration_number": (
                        trip.bus.registration_number
                    ),
                    "bus_type": trip.bus.bus_type,
                    "total_seats": trip.bus.total_seats,
                    "amenities": trip.bus.amenities,
                },
                "boarding_point": trip.boarding_point,
                "dropping_point": trip.dropping_point,
                "booking_url": trip.booking_url,
            }
            for trip in trips
        ],
    }