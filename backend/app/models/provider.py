import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ProviderKind
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.carrier import Carrier


class Provider(UUIDPrimaryKeyMixin, Base):
    """A concrete way of fetching tracking data: an official carrier API, a scraper, or a
    third-party aggregator. Several providers can support the same carrier; the user picks one
    per package."""

    __tablename__ = "providers"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[ProviderKind] = mapped_column(
        SqlEnum(ProviderKind, name="provider_kind", native_enum=False, length=20), nullable=False
    )
    requires_credentials: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_all_carriers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Free-form runtime tuning: poll intervals, rate limits, base URLs, etc. Consumed by the
    # provider implementation and the Celery dispatcher, never by the API layer directly.
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Structured onboarding instructions rendered by the frontend's "guided connections" screen:
    # {"intro": str, "steps": [{"title", "description", "link"}], "fields": [{"key","label",
    # "type","required","help_text"}]}. Null for providers that need no credentials.
    setup_guide: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    carrier_support: Mapped[list["ProviderCarrierSupport"]] = relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )
    carrier_exclusions: Mapped[list["ProviderCarrierExclusion"]] = relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )


class ProviderCarrierSupport(UUIDPrimaryKeyMixin, Base):
    """Explicit provider -> carrier support, used for official_api/scraper providers that only
    cover a handful of carriers. Aggregators (supports_all_carriers=True) do not need rows here."""

    __tablename__ = "provider_carrier_support"
    __table_args__ = (UniqueConstraint("provider_id", "carrier_id"),)

    provider_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False
    )
    carrier_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("carriers.id", ondelete="CASCADE"), nullable=False
    )

    provider: Mapped["Provider"] = relationship(back_populates="carrier_support")
    carrier: Mapped["Carrier"] = relationship(back_populates="provider_support")


class ProviderCarrierExclusion(UUIDPrimaryKeyMixin, Base):
    """Carriers a supports_all_carriers=True provider explicitly does NOT cover."""

    __tablename__ = "provider_carrier_exclusion"
    __table_args__ = (UniqueConstraint("provider_id", "carrier_id"),)

    provider_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False
    )
    carrier_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("carriers.id", ondelete="CASCADE"), nullable=False
    )

    provider: Mapped["Provider"] = relationship(back_populates="carrier_exclusions")
    carrier: Mapped["Carrier"] = relationship(back_populates="provider_exclusions")
