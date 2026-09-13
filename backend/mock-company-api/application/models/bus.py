from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.database.base import Base
from application.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from application.models.operator import Operator
    from application.models.trip import Trip


class Bus(CreatedAtMixin, Base):
    __tablename__ = "buses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    operator_id: Mapped[int] = mapped_column(
        ForeignKey("operators.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    bus_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )

    bus_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    total_seats: Mapped[int] = mapped_column(
        Integer,
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
