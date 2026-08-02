"""Shop catalogue, including carrier hints used by the add-tracker wizard."""

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.shop import Shop, ShopCarrierHint
from app.schemas.shop import ShopRead

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("", response_model=list[ShopRead])
async def list_shops(_user: CurrentUser, db: DbSession) -> list[Shop]:
    stmt = (
        select(Shop)
        .options(selectinload(Shop.carrier_hints).selectinload(ShopCarrierHint.carrier))
        .order_by(Shop.name)
    )
    return list((await db.execute(stmt)).scalars().unique().all())
