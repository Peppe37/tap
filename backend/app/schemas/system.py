from pydantic import BaseModel


class UpdateStatus(BaseModel):
    current_version: str
    latest_version: str
    update_available: bool
    release_url: str | None = None
