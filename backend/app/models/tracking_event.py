import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PackageStatus
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.package import Package
    from app.models.provider import Provider


class TrackingEvent(UUIDPrimaryKeyMixin, Base):
    """A single status update pulled from a provider for a given package."""

    __tablename__ = "tracking_events"
    __table_args__ = (UniqueConstraint("package_id", "occurred_at", "description"),)

    package_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("packages.id", ondelete="CASCADE"), nullable=False
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("providers.id"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[PackageStatus] = mapped_column(
        SqlEnum(PackageStatus, name="package_status", native_enum=False, length=20), nullable=False
    )
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    package: Mapped["Package"] = relationship(back_populates="events")
    provider: Mapped["Provider"] = relationship()
