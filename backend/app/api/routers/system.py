"""System-level endpoints: version info and the update-available check."""

from fastapi import APIRouter

from app.api.deps import CurrentAdmin
from app.core.config import get_settings
from app.schemas.system import UpdateStatus
from app.services.update_check import check_for_update

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/update-status", response_model=UpdateStatus)
async def update_status(_admin: CurrentAdmin) -> UpdateStatus:
    settings = get_settings()
    latest_version, update_available = await check_for_update()
    release_url = (
        f"https://github.com/{settings.github_repo}/releases/tag/{latest_version}"
        if update_available
        else None
    )
    return UpdateStatus(
        current_version=settings.app_version,
        latest_version=latest_version,
        update_available=update_available,
        release_url=release_url,
    )
