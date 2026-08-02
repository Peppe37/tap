from pydantic import BaseModel, Field


class CredentialStatusRead(BaseModel):
    provider_code: str
    is_configured: bool


class CredentialSetRequest(BaseModel):
    fields: dict[str, str] = Field(min_length=1)


class CredentialTestRequest(BaseModel):
    fields: dict[str, str] = Field(min_length=1)


class CredentialTestResult(BaseModel):
    is_valid: bool
