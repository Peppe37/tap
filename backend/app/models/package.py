import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PackageStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.carrier import Carrier
    from app.models.provider import Provider
    from app.models.shop import Shop
    from app.models.tracking_event import TrackingEvent
    from app.models.user import User

DEFAULT_CHECK_INTERVAL_SECONDS = 3600
MAX_CHECK_INTERVAL_SECONDS = 24 * 3600


class Package(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single tracked shipment belonging to a user."""

    __tablename__ = "packages"
    __table_args__ = (
        Index("ix_packages_user_id_is_archived", "user_id", "is_archived"),
        Index(
            "ix_packages_next_check_at_active",
            "next_check_at",
            postgresql_where=text("NOT is_archived"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tracking_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    carrier_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("carriers.id"), nullable=False
    )
    shop_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("shops.id"), nullable=True
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("providers.id"), nullable=False
    )
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Extra per-package details a provider may need beyond the tracking number itself, e.g.
    # {"destination_postal_code": "..."} for carriers that 17TRACK requires it for (Mondial
    # Relay and similar last-mile/locker networks). Most providers ignore this entirely.
    provider_params: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[PackageStatus] = mapped_column(
        SqlEnum(PackageStatus, name="package_status", native_enum=False, length=20),
        default=PackageStatus.CREATED,
        nullable=False,
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_interval_seconds: Mapped[int] = mapped_column(
        Integer, default=DEFAULT_CHECK_INTERVAL_SECONDS, nullable=False
    )
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_archived: Mapped[bool] = mapped_column(default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="packages")
    carrier: Mapped["Carrier"] = relationship()
    shop: Mapped["Shop | None"] = relationship()
    provider: Mapped["Provider"] = relationship()
    events: Mapped[list["TrackingEvent"]] = relationship(
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="TrackingEvent.occurred_at.desc()",
    )
