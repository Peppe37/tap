import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.carrier import Carrier


class Shop(UUIDPrimaryKeyMixin, Base):
    """A marketplace/retailer the user bought from (e.g. AliExpress, Amazon)."""

    __tablename__ = "shops"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    carrier_hints: Mapped[list["ShopCarrierHint"]] = relationship(
        back_populates="shop",
        cascade="all, delete-orphan",
        order_by="ShopCarrierHint.weight.desc()",
    )


class ShopCarrierHint(UUIDPrimaryKeyMixin, Base):
    """Suggests which carriers are commonly used by a given shop, to guide the add-tracker UI."""

    __tablename__ = "shop_carrier_hints"
    __table_args__ = (UniqueConstraint("shop_id", "carrier_id"),)

    shop_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False
    )
    carrier_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("carriers.id", ondelete="CASCADE"), nullable=False
    )
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    shop: Mapped["Shop"] = relationship(back_populates="carrier_hints")
    carrier: Mapped["Carrier"] = relationship(back_populates="shop_hints")
