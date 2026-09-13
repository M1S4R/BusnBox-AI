from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Common async CRUD operations for SQLAlchemy models."""

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get_by_id(
        self,
        session: AsyncSession,
        record_id: int,
    ) -> ModelType | None:
        return await session.get(self.model, record_id)

    async def get_all(
        self,
        session: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        statement = select(self.model).offset(offset).limit(limit)
        result = await session.scalars(statement)
        return list(result.all())

    async def create(
        self,
        session: AsyncSession,
        **values: object,
    ) -> ModelType:
        record = self.model(**values)
        session.add(record)

        await session.flush()
        await session.refresh(record)

        return record

    async def update(
        self,
        session: AsyncSession,
        record: ModelType,
        **values: object,
    ) -> ModelType:
        for field_name, value in values.items():
            if not hasattr(record, field_name):
                raise ValueError(
                    f"{self.model.__name__} has no field '{field_name}'"
                )

            setattr(record, field_name, value)

        await session.flush()
        await session.refresh(record)

        return record

    async def delete(
        self,
        session: AsyncSession,
        record: ModelType,
    ) -> None:
        await session.delete(record)
        await session.flush()
