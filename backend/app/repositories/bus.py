from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bus import Bus
from app.repositories.base import BaseRepository


class BusRepository(BaseRepository[Bus]):
    def __init__(self) -> None:
        super().__init__(Bus)

    async def get_by_registration_number(
        self,
        session: AsyncSession,
        registration_number: str,
    ) -> Bus | None:
        statement = (
            select(Bus)
            .options(selectinload(Bus.operator))
            .where(
                Bus.registration_number
                == registration_number.strip().upper()
            )
        )

        return await session.scalar(statement)

    async def get_by_operator_id(
        self,
        session: AsyncSession,
        operator_id: int,
    ) -> list[Bus]:
        statement = (
            select(Bus)
            .where(
                Bus.operator_id == operator_id,
                Bus.is_active.is_(True),
            )
            .order_by(Bus.bus_name)
        )

        result = await session.scalars(statement)
        return list(result.all())


bus_repository = BusRepository()
