"""Carrier catalogue and, for a given carrier, the list of tracking providers that support it."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import and_, or_, select

from app.api.deps import CurrentUser, DbSession
from app.models.carrier import Carrier
from app.models.provider import Provider, ProviderCarrierExclusion, ProviderCarrierSupport
from app.schemas.carrier import CarrierRead
from app.schemas.provider import ProviderRead

router = APIRouter(prefix="/carriers", tags=["carriers"])


@router.get("", response_model=list[CarrierRead])
async def list_carriers(_user: CurrentUser, db: DbSession) -> list[Carrier]:
    return list((await db.execute(select(Carrier).order_by(Carrier.name))).scalars().all())


@router.get("/{code}/providers", response_model=list[ProviderRead])
async def list_providers_for_carrier(
    code: str, _user: CurrentUser, db: DbSession
) -> list[Provider]:
    carrier = (await db.execute(select(Carrier).where(Carrier.code == code))).scalar_one_or_none()
    if carrier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown carrier")

    excluded = select(ProviderCarrierExclusion.provider_id).where(
        ProviderCarrierExclusion.carrier_id == carrier.id
    )
    stmt = (
        select(Provider)
        .outerjoin(
            ProviderCarrierSupport,
            and_(
                ProviderCarrierSupport.provider_id == Provider.id,
                ProviderCarrierSupport.carrier_id == carrier.id,
            ),
        )
        .where(
            Provider.is_active.is_(True),
            Provider.id.not_in(excluded),
            or_(Provider.supports_all_carriers.is_(True), ProviderCarrierSupport.id.is_not(None)),
        )
        .distinct()
        .order_by(Provider.display_name)
    )
    return list((await db.execute(stmt)).scalars().all())
