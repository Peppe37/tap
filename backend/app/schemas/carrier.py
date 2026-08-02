import uuid

from pydantic import BaseModel, ConfigDict


class CarrierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    country_code: str
