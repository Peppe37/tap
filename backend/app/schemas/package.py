import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PackageStatus
from app.schemas.carrier import CarrierRead
from app.schemas.provider import ProviderRead
from app.schemas.tracking_event import TrackingEventRead


class ShopSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str


class PackageCreate(BaseModel):
    tracking_number: str = Field(min_length=3, max_length=120)
    carrier_code: str
    provider_code: str
    shop_code: str | None = None
    label: str | None = Field(default=None, max_length=200)
    # Extra details some providers need beyond the tracking number, e.g. destination_postal_code
    # for carriers 17TRACK can only track with a postal code (Mondial Relay and similar).
    extra_params: dict[str, str] | None = None


class PackageUpdate(BaseModel):
    """All fields are optional; only the ones actually present in the request are applied
    (tracked via ``model_fields_set``), so e.g. omitting ``shop_code`` leaves it unchanged while
    sending it as ``null`` explicitly clears it."""

    label: str | None = Field(default=None, max_length=200)
    is_archived: bool | None = None
    tracking_number: str | None = Field(default=None, min_length=3, max_length=120)
    carrier_code: str | None = None
    provider_code: str | None = None
    shop_code: str | None = None
    extra_params: dict[str, str] | None = None


class PackageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tracking_number: str
    label: str | None
    status: PackageStatus
    last_checked_at: datetime | None
    next_check_at: datetime | None
    is_archived: bool
    created_at: datetime
    carrier: CarrierRead
    shop: ShopSummaryRead | None
    provider: ProviderRead
    extra_params: dict[str, str] | None = Field(default=None, validation_alias="provider_params")


class PackageDetailRead(PackageRead):
    events: list[TrackingEventRead] = []
