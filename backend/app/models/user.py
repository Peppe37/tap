from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.credential import UserProviderCredential
    from app.models.package import Package


class User(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    packages: Mapped[list["Package"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    provider_credentials: Mapped[list["UserProviderCredential"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
