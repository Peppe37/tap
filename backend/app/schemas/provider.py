import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import ProviderKind


class ProviderSetupGuideField(BaseModel):
    key: str
    label: str
    type: str
    required: bool
    help_text: str | None = None


class ProviderSetupGuideStep(BaseModel):
    title: str
    description: str
    link: str | None = None


class ProviderSetupGuide(BaseModel):
    intro: str
    steps: list[ProviderSetupGuideStep] = []
    fields: list[ProviderSetupGuideField] = []


class ProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    display_name: str
    kind: ProviderKind
    requires_credentials: bool
    setup_guide: ProviderSetupGuide | None = None
