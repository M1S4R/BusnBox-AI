from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import engine


async def check_database_connection() -> bool:
    """Check whether SQLAlchemy can communicate with MariaDB."""

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            return result.scalar_one() == 1
    except SQLAlchemyError as exc:
        print(f"Database error: {exc}")
        return False