"""Mapping from 17TRACK's nine main tracking statuses to the platform's normalized status.

Source: 17TRACK API v2.x reference, "latest_status.status" enum
(https://asset.17track.net/api/document/v2.2_en/index.html).
"""

from app.models.enums import PackageStatus

STATUS_MAP: dict[str, PackageStatus] = {
    "NotFound": PackageStatus.UNKNOWN,
    "InfoReceived": PackageStatus.CREATED,
    "InTransit": PackageStatus.IN_TRANSIT,
    "Expired": PackageStatus.EXCEPTION,
    "AvailableForPickup": PackageStatus.IN_TRANSIT,
    "OutForDelivery": PackageStatus.OUT_FOR_DELIVERY,
    "DeliveryFailure": PackageStatus.EXCEPTION,
    "Delivered": PackageStatus.DELIVERED,
    "Exception": PackageStatus.EXCEPTION,
}
