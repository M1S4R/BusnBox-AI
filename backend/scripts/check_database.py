import asyncio

from app.core.config import settings
from app.database.connection import dispose_database_engine
from app.database.health import check_database_connection


async def main() -> int:
    print(f"Checking database: {settings.safe_database_url}")

    is_connected = await check_database_connection()

    await dispose_database_engine()

    if not is_connected:
        print("Database connection failed.")
        return 1

    print("Database connection successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))