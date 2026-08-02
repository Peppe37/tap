"""Free-text status classification for Poste Italiane's "Dove Quando" tracking responses.

Poste Italiane does not publish a stable status-code enum for this endpoint (unlike InPost's
documented ShipX API) -- "sintesiStato" and "statoLavorazione" are Italian prose describing the
event. We classify them with ordered keyword matching; anything unrecognised maps to UNKNOWN
rather than being guessed.
"""

from app.models.enums import PackageStatus
from app.providers.status import map_by_keywords

_KEYWORD_TABLE: list[tuple[tuple[str, ...], PackageStatus]] = [
    (
        ("consegnat", "ritirato dal destinatario", "ritirata dal destinatario"),
        PackageStatus.DELIVERED,
    ),
    (
        (
            "giacenza",
            "mancata consegna",
            "non ritirat",
            "respint",
            "smarrit",
            "furto",
            "danneggiat",
            "rifiutat",
            "irreperibil",
            "non consegnat",
        ),
        PackageStatus.EXCEPTION,
    ),
    (
        (
            "in consegna",
            "affidato al portalettere",
            "affidata al portalettere",
            "uscito per la consegna",
        ),
        PackageStatus.OUT_FOR_DELIVERY,
    ),
    (
        (
            "in transito",
            "instradat",
            "lavorazione",
            "partit",
            "arrivat",
            "in viaggio",
            "presa in carico",
            "accettazione",
            "sportello",
        ),
        PackageStatus.IN_TRANSIT,
    ),
]


def classify(status_text: str | None) -> PackageStatus:
    if not status_text:
        return PackageStatus.UNKNOWN
    return map_by_keywords(status_text, _KEYWORD_TABLE)
