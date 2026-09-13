from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operator import Operator
from app.repositories.base import BaseRepository


class OperatorRepository(BaseRepository[Operator]):
    def __init__(self) -> None:
        super().__init__(Operator)

    async def get_by_code(
        self,
        session: AsyncSession,
        code: str,
    ) -> Operator | None:
        statement = select(Operator).where(
            func.lower(Operator.code) == code.strip().lower()
        )
        return await session.scalar(statement)

    async def get_by_name(
        self,
        session: AsyncSession,
        name: str,
    ) -> Operator | None:
        statement = select(Operator).where(
            func.lower(Operator.name) == name.strip().lower()
        )
        return await session.scalar(statement)


operator_repository = OperatorRepository()
