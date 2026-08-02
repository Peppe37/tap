import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import PackageStatus


class TrackingEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    occurred_at: datetime
    status: PackageStatus
    location: str | None
    description: str
