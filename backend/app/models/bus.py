from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.operator import Operator
    from app.models.trip import Trip


class Bus(TimestampMixin, Base):
    __tablename__ = "buses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    operator_id: Mapped[int] = mapped_column(
        ForeignKey("operators.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    registration_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    bus_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    bus_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    total_seats: Mapped[int] = mapped_column(
        nullable=False,
    )

    amenities: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    operator: Mapped["Operator"] = relationship(
        back_populates="buses",
    )

    trips: Mapped[list["Trip"]] = relationship(
        back_populates="bus",
    )

    def __repr__(self) -> str:
        return (
            f"Bus(id={self.id!r}, registration_number="
            f"{self.registration_number!r})"
        )
