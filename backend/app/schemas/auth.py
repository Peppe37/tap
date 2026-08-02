from pydantic import BaseModel, EmailStr, Field


class SetupStatus(BaseModel):
    needs_setup: bool


class SetupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=72)
    is_admin: bool = False


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
