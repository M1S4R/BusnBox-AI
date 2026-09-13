from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.database.base import Base
from application.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from application.models.bus import Bus
    from application.models.route import Route


class Trip(TimestampMixin, Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    trip_code: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False,
    )

    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id"),
        index=True,
        nullable=False,
    )

    bus_id: Mapped[int] = mapped_column(
        ForeignKey("buses.id"),
        index=True,
        nullable=False,
    )

    travel_date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )

    departure_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )

    arrival_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    available_seats: Mapped[int] = mapped_column(
        nullable=False,
    )

    boarding_point: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    dropping_point: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    booking_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="scheduled",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    route: Mapped["Route"] = relationship(
        back_populates="trips",
    )

    bus: Mapped["Bus"] = relationship(
        back_populates="trips",
    )

    def __repr__(self) -> str:
        return (
            f"Trip(id={self.id!r}, route_id={self.route_id!r}, "
            f"departure_time={self.departure_time!r})"
        )
