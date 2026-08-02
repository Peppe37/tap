"""CRUD for tracked packages plus the on-demand refresh endpoint that calls the chosen provider."""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.carrier import Carrier
from app.models.package import Package
from app.models.provider import Provider, ProviderCarrierExclusion, ProviderCarrierSupport
from app.models.shop import Shop
from app.providers.base import ProviderNotConfiguredError
from app.providers.registry import provider_registry
from app.schemas.package import PackageCreate, PackageDetailRead, PackageRead, PackageUpdate
from app.services.credentials import load_credentials
from app.services.tracking import apply_tracking_result, reset_for_retarget

router = APIRouter(prefix="/packages", tags=["packages"])

_EAGER_LOAD = (
    selectinload(Package.carrier),
    selectinload(Package.shop),
    selectinload(Package.provider),
    selectinload(Package.events),
)


async def _get_owned_package_or_404(
    db: DbSession, user_id: uuid.UUID, package_id: uuid.UUID
) -> Package:
    # populate_existing forces already-identity-mapped relationships (e.g. events loaded before
    # a refresh added new rows in this same session) to be reloaded from the database.
    package = (
        await db.execute(
            select(Package)
            .where(Package.id == package_id)
            .options(*_EAGER_LOAD)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if package is None or package.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return package


async def _get_carrier_by_code_or_404(db: DbSession, code: str) -> Carrier:
    carrier = (await db.execute(select(Carrier).where(Carrier.code == code))).scalar_one_or_none()
    if carrier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown carrier")
    return carrier


async def _get_provider_by_code_or_404(db: DbSession, code: str) -> Provider:
    provider = (
        await db.execute(select(Provider).where(Provider.code == code))
    ).scalar_one_or_none()
    if provider is None or not provider.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown provider")
    return provider


async def _get_shop_by_code_or_404(db: DbSession, code: str) -> Shop:
    shop = (await db.execute(select(Shop).where(Shop.code == code))).scalar_one_or_none()
    if shop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown shop")
    return shop


async def _provider_supports_carrier(db: DbSession, provider: Provider, carrier: Carrier) -> bool:
    excluded = (
        await db.execute(
            select(ProviderCarrierExclusion).where(
                ProviderCarrierExclusion.provider_id == provider.id,
                ProviderCarrierExclusion.carrier_id == carrier.id,
            )
        )
    ).scalar_one_or_none()
    if excluded is not None:
        return False
    if provider.supports_all_carriers:
        return True
    support = (
        await db.execute(
            select(ProviderCarrierSupport).where(
                ProviderCarrierSupport.provider_id == provider.id,
                ProviderCarrierSupport.carrier_id == carrier.id,
            )
        )
    ).scalar_one_or_none()
    return support is not None


@router.post("", response_model=PackageDetailRead, status_code=status.HTTP_201_CREATED)
async def create_package(payload: PackageCreate, user: CurrentUser, db: DbSession) -> Package:
    carrier = await _get_carrier_by_code_or_404(db, payload.carrier_code)
    provider = await _get_provider_by_code_or_404(db, payload.provider_code)

    if not await _provider_supports_carrier(db, provider, carrier):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This provider does not support the selected carrier",
        )

    shop: Shop | None = None
    if payload.shop_code is not None:
        shop = await _get_shop_by_code_or_404(db, payload.shop_code)

    package = Package(
        user_id=user.id,
        tracking_number=payload.tracking_number,
        carrier_id=carrier.id,
        shop_id=shop.id if shop else None,
        provider_id=provider.id,
        label=payload.label,
        provider_params=payload.extra_params,
    )
    db.add(package)
    await db.commit()
    return await _get_owned_package_or_404(db, user.id, package.id)


@router.get("", response_model=list[PackageRead])
async def list_packages(
    user: CurrentUser, db: DbSession, include_archived: bool = False
) -> list[Package]:
    stmt = select(Package).where(Package.user_id == user.id).options(*_EAGER_LOAD)
    if not include_archived:
        stmt = stmt.where(Package.is_archived.is_(False))
    stmt = stmt.order_by(Package.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{package_id}", response_model=PackageDetailRead)
async def get_package(package_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Package:
    return await _get_owned_package_or_404(db, user.id, package_id)


@router.patch("/{package_id}", response_model=PackageDetailRead)
async def update_package(
    package_id: uuid.UUID, payload: PackageUpdate, user: CurrentUser, db: DbSession
) -> Package:
    package = await _get_owned_package_or_404(db, user.id, package_id)
    fields = payload.model_fields_set

    new_carrier = package.carrier
    new_provider = package.provider
    touches_targeting = {"tracking_number", "carrier_code", "provider_code"} & fields

    if "carrier_code" in fields:
        assert payload.carrier_code is not None
        new_carrier = await _get_carrier_by_code_or_404(db, payload.carrier_code)
    if "provider_code" in fields:
        assert payload.provider_code is not None
        new_provider = await _get_provider_by_code_or_404(db, payload.provider_code)
    if touches_targeting and not await _provider_supports_carrier(db, new_provider, new_carrier):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This provider does not support the selected carrier",
        )

    # Only reset tracking history when a value actually changes -- the frontend's edit form
    # resubmits every field on every save, so presence alone (unlike shop_code's clear-vs-unset
    # distinction) would otherwise wipe history on a no-op save (e.g. renaming the label).
    is_retarget = (
        ("tracking_number" in fields and payload.tracking_number != package.tracking_number)
        or ("carrier_code" in fields and new_carrier.id != package.carrier_id)
        or ("provider_code" in fields and new_provider.id != package.provider_id)
    )

    if "shop_code" in fields:
        package.shop_id = (
            (await _get_shop_by_code_or_404(db, payload.shop_code)).id
            if payload.shop_code is not None
            else None
        )
    if "tracking_number" in fields:
        assert payload.tracking_number is not None
        package.tracking_number = payload.tracking_number
    if "carrier_code" in fields:
        package.carrier_id = new_carrier.id
    if "provider_code" in fields:
        package.provider_id = new_provider.id
    if "extra_params" in fields:
        package.provider_params = payload.extra_params
    if "label" in fields:
        package.label = payload.label
    if "is_archived" in fields:
        assert payload.is_archived is not None
        package.is_archived = payload.is_archived

    if is_retarget:
        reset_for_retarget(package)

    await db.commit()
    return await _get_owned_package_or_404(db, user.id, package.id)


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(package_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    package = await _get_owned_package_or_404(db, user.id, package_id)
    await db.delete(package)
    await db.commit()


@router.post("/{package_id}/refresh", response_model=PackageDetailRead)
async def refresh_package(package_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Package:
    package = await _get_owned_package_or_404(db, user.id, package_id)
    implementation = provider_registry.get(package.provider.code)

    credentials: dict[str, str] | None = None
    if implementation.requires_credentials:
        credentials = await load_credentials(db, user_id=user.id, provider_id=package.provider_id)
        if credentials is None:
            raise ProviderNotConfiguredError(
                f"Configure credentials for {package.provider.display_name} before refreshing"
            )

    result = await implementation.fetch(
        package.tracking_number, package.carrier.code, credentials, package.provider_params
    )
    apply_tracking_result(package, result)

    await db.commit()
    return await _get_owned_package_or_404(db, user.id, package.id)
