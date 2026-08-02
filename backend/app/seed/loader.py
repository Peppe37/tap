"""Idempotent seed data loader: populates carriers, shops, shop-carrier hints and providers from
the YAML fixtures in this package. Safe to run repeatedly (upserts by natural code, never
duplicates). Run with ``python -m app.seed.loader``.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.carrier import Carrier
from app.models.enums import ProviderKind
from app.models.provider import Provider, ProviderCarrierSupport
from app.models.shop import Shop, ShopCarrierHint

logger = logging.getLogger(__name__)
SEED_DIR = Path(__file__).parent


def _load_yaml(filename: str) -> Any:
    with (SEED_DIR / filename).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


async def _seed_carriers(session: AsyncSession) -> dict[str, Carrier]:
    by_code: dict[str, Carrier] = {}
    for entry in _load_yaml("carriers.yaml"):
        carrier = (
            await session.execute(select(Carrier).where(Carrier.code == entry["code"]))
        ).scalar_one_or_none()
        if carrier is None:
            carrier = Carrier(code=entry["code"])
            session.add(carrier)
        carrier.name = entry["name"]
        carrier.country_code = entry["country_code"]
        by_code[entry["code"]] = carrier
    await session.flush()
    return by_code


async def _seed_shops(session: AsyncSession) -> dict[str, Shop]:
    by_code: dict[str, Shop] = {}
    for entry in _load_yaml("shops.yaml"):
        shop = (
            await session.execute(select(Shop).where(Shop.code == entry["code"]))
        ).scalar_one_or_none()
        if shop is None:
            shop = Shop(code=entry["code"])
            session.add(shop)
        shop.name = entry["name"]
        by_code[entry["code"]] = shop
    await session.flush()
    return by_code


async def _seed_shop_carrier_hints(
    session: AsyncSession, shops: dict[str, Shop], carriers: dict[str, Carrier]
) -> None:
    hints_by_shop: dict[str, list[dict[str, Any]]] = _load_yaml("shop_carrier_hints.yaml")
    for shop_code, hints in hints_by_shop.items():
        shop = shops[shop_code]
        for hint in hints:
            carrier = carriers[hint["carrier"]]
            existing = (
                await session.execute(
                    select(ShopCarrierHint).where(
                        ShopCarrierHint.shop_id == shop.id,
                        ShopCarrierHint.carrier_id == carrier.id,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    ShopCarrierHint(shop_id=shop.id, carrier_id=carrier.id, weight=hint["weight"])
                )
            else:
                existing.weight = hint["weight"]
    await session.flush()


async def _seed_providers(session: AsyncSession, carriers: dict[str, Carrier]) -> None:
    for entry in _load_yaml("providers.yaml"):
        provider = (
            await session.execute(select(Provider).where(Provider.code == entry["code"]))
        ).scalar_one_or_none()
        if provider is None:
            provider = Provider(code=entry["code"])
            session.add(provider)
        provider.display_name = entry["display_name"]
        provider.kind = ProviderKind(entry["kind"])
        provider.requires_credentials = entry["requires_credentials"]
        provider.supports_all_carriers = entry["supports_all_carriers"]
        provider.setup_guide = entry.get("setup_guide")
        provider.is_active = True
        await session.flush()

        existing_support = (
            (
                await session.execute(
                    select(ProviderCarrierSupport).where(
                        ProviderCarrierSupport.provider_id == provider.id
                    )
                )
            )
            .scalars()
            .all()
        )
        existing_carrier_ids = {row.carrier_id for row in existing_support}

        for carrier_code in entry.get("carriers", []):
            carrier = carriers[carrier_code]
            if carrier.id not in existing_carrier_ids:
                session.add(ProviderCarrierSupport(provider_id=provider.id, carrier_id=carrier.id))
    await session.flush()


async def seed(session: AsyncSession) -> None:
    carriers = await _seed_carriers(session)
    shops = await _seed_shops(session)
    await _seed_shop_carrier_hints(session, shops, carriers)
    await _seed_providers(session, carriers)
    await session.commit()
    logger.info(
        "seed complete: %d carriers, %d shops",
        len(carriers),
        len(shops),
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    async with AsyncSessionLocal() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
