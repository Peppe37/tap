"""Mapping from tap's internal carrier codes to 17TRACK's numeric carrier ids.

17TRACK can auto-detect a carrier from the tracking number's format alone when no `carrier` id is
given, but auto-detection fails outright for many carriers whose numbers are short/generic (e.g.
Mondial Relay's are plain digit strings indistinguishable from several other carriers) -- the API
then rejects the number at the *registration* step with "Carrier cannot be detected", and every
subsequent lookup fails too. Passing the numeric id sidesteps auto-detection entirely.

IDs below were looked up in 17TRACK's published carrier list
(https://res.17track.net/asset/carrier/info/apicarrier.all.json) and cross-checked against the
country each entry lists. Carriers are deliberately left out when 17TRACK has multiple
region-specific entries and it wasn't possible to confirm which one matches our carrier's
country (e.g. GLS) -- an incorrect id would silently query the wrong carrier's data, which is
worse than falling back to auto-detection.
"""

SEVENTEEN_TRACK_CARRIER_IDS: dict[str, int] = {
    "mondial_relay": 100304,  # Mondial Relay, FR
    "nexive": 100087,  # Nexive / Poste Delivery Business, IT
    "poste_it": 9071,  # Poste Italiane, IT
    "inpost": 100043,  # InPost, PL
    "correos": 19181,  # Correos, ES
    "postnl": 14041,  # PostNL, NL
    "colissimo": 6051,  # La Poste / Colissimo, FR
    "china_post": 3011,  # China Post, CN
    "dhl": 100001,  # DHL Express, DE
    "ups": 100002,  # UPS, US
    "fedex": 100003,  # FedEx, US
    "hermes": 100331,  # EVRi (formerly Hermes), GB
    "sda": 100019,  # SDA Express Courier, IT
    "brt": 100026,  # BRT (Bartolini), IT
    "tnt": 100004,  # TNT
    "dpd": 100031,  # DPD, DE
}


def seventeen_track_carrier_id(carrier_code: str) -> int | None:
    return SEVENTEEN_TRACK_CARRIER_IDS.get(carrier_code)
