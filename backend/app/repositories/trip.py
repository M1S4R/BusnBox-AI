from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bus import Bus
from app.models.route import Route
from app.models.trip import Trip
from app.repositories.base import BaseRepository


class TripRepository(BaseRepository[Trip]):
    def __init__(self) -> None:
        super().__init__(Trip)

    async def get_with_details(
        self,
        session: AsyncSession,
        trip_id: int,
    ) -> Trip | None:
        statement = (
            select(Trip)
            .options(
                selectinload(Trip.bus).selectinload(Bus.operator),
                selectinload(Trip.route).selectinload(Route.source_city),
                selectinload(Trip.route).selectinload(
                    Route.destination_city
                ),
            )
            .where(Trip.id == trip_id)
        )

        return await session.scalar(statement)

    async def search_available_trips(
        self,
        session: AsyncSession,
        *,
        source_city_id: int,
        destination_city_id: int,
        departure_from: datetime,
        departure_until: datetime,
        minimum_seats: int = 1,
        limit: int = 50,
    ) -> list[Trip]:
        statement = (
            select(Trip)
            .join(Trip.route)
            .options(
                selectinload(Trip.bus).selectinload(Bus.operator),
                selectinload(Trip.route).selectinload(Route.source_city),
                selectinload(Trip.route).selectinload(
                    Route.destination_city
                ),
            )
            .where(
                Route.source_city_id == source_city_id,
                Route.destination_city_id == destination_city_id,
                Route.is_active.is_(True),
                Trip.departure_time >= departure_from,
                Trip.departure_time < departure_until,
                Trip.available_seats >= minimum_seats,
                Trip.status == "scheduled",
                Trip.is_active.is_(True),
            )
            .order_by(Trip.departure_time, Trip.price)
            .limit(limit)
        )

        result = await session.scalars(statement)
        return list(result.unique().all())


trip_repository = TripRepository()
