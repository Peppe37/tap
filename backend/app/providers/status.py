"""Helpers shared by provider adapters for mapping carrier-specific status strings onto the
platform's normalized :class:`~app.models.enums.PackageStatus`."""

from app.models.enums import PackageStatus

# Re-exported under the name used in the architecture docs/plan; it is the same enum used by the
# Package/TrackingEvent ORM models, so a provider's output can be persisted without translation.
NormalizedStatus = PackageStatus


def map_exact(raw_status: str, table: dict[str, PackageStatus]) -> PackageStatus:
    """Look up an exact carrier status code in a static mapping table."""
    return table.get(raw_status, PackageStatus.UNKNOWN)


def map_by_keywords(
    text: str, keyword_table: list[tuple[tuple[str, ...], PackageStatus]]
) -> PackageStatus:
    """Match free-text status descriptions (e.g. scraped Italian prose) against ordered
    keyword groups, returning the first match. Intended for carriers with no stable status
    enum, where exact-code mapping is not possible."""
    lowered = text.lower()
    for keywords, status in keyword_table:
        if any(keyword in lowered for keyword in keywords):
            return status
    return PackageStatus.UNKNOWN
