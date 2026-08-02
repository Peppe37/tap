import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_secret
from app.models.credential import UserProviderCredential


async def load_credentials(
    db: AsyncSession, *, user_id: uuid.UUID, provider_id: uuid.UUID
) -> dict[str, str] | None:
    credential = (
        await db.execute(
            select(UserProviderCredential).where(
                UserProviderCredential.user_id == user_id,
                UserProviderCredential.provider_id == provider_id,
            )
        )
    ).scalar_one_or_none()
    if credential is None:
        return None
    fields: dict[str, str] = json.loads(decrypt_secret(credential.encrypted_secret))
    return fields
