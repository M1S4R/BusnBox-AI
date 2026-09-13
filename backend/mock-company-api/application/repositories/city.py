from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.city import City
from application.repositories.base import BaseRepository


class CityRepository(BaseRepository[City]):
    def __init__(self) -> None:
        super().__init__(City)

    async def get_by_code(
        self,
        session: AsyncSession,
        code: str,
    ) -> City | None:
        statement = select(City).where(
            func.lower(City.code) == code.strip().lower()
        )
        return await session.scalar(statement)

    async def get_by_name(
        self,
        session: AsyncSession,
        name: str,
    ) -> City | None:
        statement = select(City).where(
            func.lower(City.name) == name.strip().lower()
        )
        return await session.scalar(statement)

    async def search_by_name(
        self,
        session: AsyncSession,
        query: str,
        *,
        limit: int = 20,
    ) -> list[City]:
        statement = (
            select(City)
            .where(
                City.is_active.is_(True),
                City.name.ilike(f"%{query.strip()}%"),
            )
            .order_by(City.name)
            .limit(limit)
        )

        result = await session.scalars(statement)
        return list(result.all())


city_repository = CityRepository()
