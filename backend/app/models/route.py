from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.trip import Trip


class Route(TimestampMixin, Base):
    __tablename__ = "routes"

    __table_args__ = (
        UniqueConstraint(
            "source_city_id",
            "destination_city_id",
            name="uq_route_source_destination",
        ),
    )

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

    route_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    distance_km: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )

    estimated_duration_minutes: Mapped[int | None] = mapped_column(
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
