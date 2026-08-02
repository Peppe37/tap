"""Provider catalogue and per-user credential management for the guided "Connections" settings
screen: providers that require credentials expose a setup_guide, plus test/save/delete
endpoints for the encrypted secret."""

import json

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.encryption import encrypt_secret
from app.models.credential import UserProviderCredential
from app.models.provider import Provider
from app.providers.base import ProviderError
from app.providers.registry import provider_registry
from app.schemas.credential import (
    CredentialSetRequest,
    CredentialStatusRead,
    CredentialTestRequest,
    CredentialTestResult,
)
from app.schemas.provider import ProviderRead

router = APIRouter(prefix="/providers", tags=["providers"])


async def _get_provider_or_404(db: DbSession, code: str) -> Provider:
    provider = (
        await db.execute(select(Provider).where(Provider.code == code))
    ).scalar_one_or_none()
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown provider")
    return provider


@router.get("", response_model=list[ProviderRead])
async def list_providers(_user: CurrentUser, db: DbSession) -> list[Provider]:
    return list(
        (await db.execute(select(Provider).where(Provider.is_active.is_(True)))).scalars().all()
    )


@router.get("/{code}/credential-status", response_model=CredentialStatusRead)
async def credential_status(code: str, user: CurrentUser, db: DbSession) -> CredentialStatusRead:
    provider = await _get_provider_or_404(db, code)
    credential = (
        await db.execute(
            select(UserProviderCredential).where(
                UserProviderCredential.user_id == user.id,
                UserProviderCredential.provider_id == provider.id,
            )
        )
    ).scalar_one_or_none()
    return CredentialStatusRead(provider_code=code, is_configured=credential is not None)


@router.post("/{code}/test-credential", response_model=CredentialTestResult)
async def test_credential(
    code: str, payload: CredentialTestRequest, _user: CurrentUser, db: DbSession
) -> CredentialTestResult:
    provider = await _get_provider_or_404(db, code)
    if not provider.requires_credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This provider does not use credentials",
        )
    implementation = provider_registry.get(code)
    try:
        is_valid = await implementation.test_credentials(payload.fields)
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return CredentialTestResult(is_valid=is_valid)


@router.put("/{code}/credential", status_code=status.HTTP_204_NO_CONTENT)
async def set_credential(
    code: str, payload: CredentialSetRequest, user: CurrentUser, db: DbSession
) -> None:
    provider = await _get_provider_or_404(db, code)
    if not provider.requires_credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This provider does not use credentials",
        )

    encrypted = encrypt_secret(json.dumps(payload.fields))
    credential = (
        await db.execute(
            select(UserProviderCredential).where(
                UserProviderCredential.user_id == user.id,
                UserProviderCredential.provider_id == provider.id,
            )
        )
    ).scalar_one_or_none()
    if credential is None:
        db.add(
            UserProviderCredential(
                user_id=user.id, provider_id=provider.id, encrypted_secret=encrypted
            )
        )
    else:
        credential.encrypted_secret = encrypted
    await db.commit()


@router.delete("/{code}/credential", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(code: str, user: CurrentUser, db: DbSession) -> None:
    provider = await _get_provider_or_404(db, code)
    credential = (
        await db.execute(
            select(UserProviderCredential).where(
                UserProviderCredential.user_id == user.id,
                UserProviderCredential.provider_id == provider.id,
            )
        )
    ).scalar_one_or_none()
    if credential is not None:
        await db.delete(credential)
        await db.commit()
