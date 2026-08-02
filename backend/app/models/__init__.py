"""Import every ORM model so SQLAlchemy's mapper registry and Alembic autogenerate see them."""

from app.models.carrier import Carrier
from app.models.credential import UserProviderCredential
from app.models.enums import PackageStatus, ProviderKind
from app.models.package import Package
from app.models.provider import Provider, ProviderCarrierExclusion, ProviderCarrierSupport
from app.models.shop import Shop, ShopCarrierHint
from app.models.tracking_event import TrackingEvent
from app.models.user import User

__all__ = [
    "Carrier",
    "Package",
    "PackageStatus",
    "Provider",
    "ProviderCarrierExclusion",
    "ProviderCarrierSupport",
    "ProviderKind",
    "Shop",
    "ShopCarrierHint",
    "TrackingEvent",
    "User",
    "UserProviderCredential",
]
