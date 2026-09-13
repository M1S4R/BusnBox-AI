import asyncio

from app.database.base import Base
from app.database.connection import dispose_database_engine, engine
from app.models import Bus, City, Operator, Route, Trip


async def create_tables() -> None:
    print("Creating database tables...")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    print("Database tables created successfully.")
    print("Tables:", ", ".join(sorted(Base.metadata.tables.keys())))


async def main() -> None:
    try:
        await create_tables()
    finally:
        await dispose_database_engine()


if __name__ == "__main__":
    asyncio.run(main())
