from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.provider import ProviderCarrierExclusion, ProviderCarrierSupport
    from app.models.shop import ShopCarrierHint


class Carrier(UUIDPrimaryKeyMixin, Base):
    """A shipping/delivery company (e.g. BRT, GLS, Poste Italiane, InPost)."""

    __tablename__ = "carriers"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    tracking_url_template: Mapped[str | None] = mapped_column(String(500), nullable=True)

    shop_hints: Mapped[list["ShopCarrierHint"]] = relationship(
        back_populates="carrier", cascade="all, delete-orphan"
    )
    provider_support: Mapped[list["ProviderCarrierSupport"]] = relationship(
        back_populates="carrier", cascade="all, delete-orphan"
    )
    provider_exclusions: Mapped[list["ProviderCarrierExclusion"]] = relationship(
        back_populates="carrier", cascade="all, delete-orphan"
    )
