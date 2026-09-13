from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.database.base import Base
from application.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from application.models.route import Route


class City(CreatedAtMixin, Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    outgoing_routes: Mapped[list["Route"]] = relationship(
        back_populates="source_city",
        foreign_keys="Route.source_city_id",
    )

    incoming_routes: Mapped[list["Route"]] = relationship(
        back_populates="destination_city",
        foreign_keys="Route.destination_city_id",
    )

    def __repr__(self) -> str:
        return f"City(id={self.id!r}, name={self.name!r}, code={self.code!r})"
