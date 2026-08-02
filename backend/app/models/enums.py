"""Shared enums used across ORM models, schemas and the provider plugin layer."""

from enum import StrEnum


class ProviderKind(StrEnum):
    OFFICIAL_API = "official_api"
    SCRAPER = "scraper"
    AGGREGATOR = "aggregator"


class PackageStatus(StrEnum):
    CREATED = "created"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    UNKNOWN = "unknown"
