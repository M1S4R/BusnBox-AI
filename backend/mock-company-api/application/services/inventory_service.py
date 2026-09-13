from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.models.bus import Bus
from application.models.route import Route
from application.models.trip import Trip


CITY_ALIASES = {
    "bangalore": "bengaluru",
    "bengaluru": "bengaluru",
    "chennai": "chennai",
    "madras": "chennai",
    "bombay": "mumbai",
    "mumbai": "mumbai",
    "mysore": "mysuru",
    "mysuru": "mysuru",
}


class InventoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_trips(
        self,
        source: str,
        destination: str,
        travel_date: date,
    ) -> list[Trip]:
        statement = (
            select(Trip)
            .options(
                selectinload(Trip.route).selectinload(Route.source_city),
                selectinload(Trip.route).selectinload(Route.destination_city),
                selectinload(Trip.bus).selectinload(Bus.operator),
            )
            .where(
                Trip.travel_date == travel_date,
            )
        )

        result = await self.session.execute(statement)
        trips = result.scalars().all()

        norm_source = CITY_ALIASES.get(source.casefold(), source.casefold())
        norm_destination = CITY_ALIASES.get(destination.casefold(), destination.casefold())

        return [
            trip
            for trip in trips
            if CITY_ALIASES.get(trip.route.source_city.name.casefold(), trip.route.source_city.name.casefold()) == norm_source
            and CITY_ALIASES.get(trip.route.destination_city.name.casefold(), trip.route.destination_city.name.casefold()) == norm_destination
        ]