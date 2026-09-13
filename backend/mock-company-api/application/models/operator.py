from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.database.base import Base
from application.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from application.models.bus import Bus


class Operator(CreatedAtMixin, Base):
    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    rating: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("4.00"),
        nullable=False,
    )

    support_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    buses: Mapped[list["Bus"]] = relationship(
        back_populates="operator",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Operator(id={self.id!r}, name={self.name!r})"
