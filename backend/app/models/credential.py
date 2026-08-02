import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.provider import Provider
    from app.models.user import User


class UserProviderCredential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user's own credentials for a provider that requires them (e.g. an aggregator API key),
    encrypted at rest with the server-side Fernet key. Never exposed decrypted via the API."""

    __tablename__ = "user_provider_credentials"
    __table_args__ = (UniqueConstraint("user_id", "provider_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False
    )
    encrypted_secret: Mapped[str] = mapped_column(String(4000), nullable=False)

    user: Mapped["User"] = relationship(back_populates="provider_credentials")
    provider: Mapped["Provider"] = relationship()
