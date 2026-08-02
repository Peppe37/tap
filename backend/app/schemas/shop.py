import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.carrier import CarrierRead


class ShopCarrierHintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    carrier: CarrierRead
    weight: int


class ShopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    carrier_hints: list[ShopCarrierHintRead] = []
