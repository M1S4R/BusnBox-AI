from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.database.base import Base
from application.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from application.models.city import City
    from application.models.trip import Trip


class Route(CreatedAtMixin, Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    source_city_id: Mapped[int] = mapped_column(
        ForeignKey("cities.id"),
        index=True,
        nullable=False,
    )

    destination_city_id: Mapped[int] = mapped_column(
        ForeignKey("cities.id"),
        index=True,
        nullable=False,
    )

    distance_km: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    estimated_duration_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    source_city: Mapped["City"] = relationship(
        back_populates="outgoing_routes",
        foreign_keys=[source_city_id],
    )

    destination_city: Mapped["City"] = relationship(
        back_populates="incoming_routes",
        foreign_keys=[destination_city_id],
    )

    trips: Mapped[list["Trip"]] = relationship(
        back_populates="route",
    )

    def __repr__(self) -> str:
        return (
            f"Route(id={self.id!r}, source_city_id={self.source_city_id!r}, "
            f"destination_city_id={self.destination_city_id!r})"
        )
