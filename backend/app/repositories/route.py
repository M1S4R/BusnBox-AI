from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.route import Route
from app.repositories.base import BaseRepository


class RouteRepository(BaseRepository[Route]):
    def __init__(self) -> None:
        super().__init__(Route)

    async def get_by_code(
        self,
        session: AsyncSession,
        route_code: str,
    ) -> Route | None:
        statement = (
            select(Route)
            .options(
                selectinload(Route.source_city),
                selectinload(Route.destination_city),
            )
            .where(Route.route_code == route_code.strip().upper())
        )

        return await session.scalar(statement)

    async def get_by_cities(
        self,
        session: AsyncSession,
        source_city_id: int,
        destination_city_id: int,
    ) -> Route | None:
        statement = (
            select(Route)
            .options(
                selectinload(Route.source_city),
                selectinload(Route.destination_city),
            )
            .where(
                Route.source_city_id == source_city_id,
                Route.destination_city_id == destination_city_id,
                Route.is_active.is_(True),
            )
        )

        return await session.scalar(statement)


route_repository = RouteRepository()
