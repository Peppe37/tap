"""Shared logic for applying a provider's fetch result onto a Package, used by both the
on-demand API refresh endpoint and the Celery polling task so scheduling stays consistent
regardless of who triggered the check."""

from datetime import UTC, datetime, timedelta

from app.models.enums import PackageStatus
from app.models.package import (
    DEFAULT_CHECK_INTERVAL_SECONDS,
    MAX_CHECK_INTERVAL_SECONDS,
    Package,
)
from app.models.tracking_event import TrackingEvent
from app.providers.base import TrackingResult

OUT_FOR_DELIVERY_CHECK_INTERVAL_SECONDS = 300


def _next_interval_for_status(status: PackageStatus) -> int:
    if status == PackageStatus.OUT_FOR_DELIVERY:
        return OUT_FOR_DELIVERY_CHECK_INTERVAL_SECONDS
    return DEFAULT_CHECK_INTERVAL_SECONDS


def apply_tracking_result(package: Package, result: TrackingResult) -> None:
    """Update status, append new (deduplicated) events, and schedule the next check.

    Polling stops once a package is delivered (next_check_at is cleared); it speeds up while
    out for delivery and otherwise falls back to the default interval.
    """
    package.status = result.status
    package.last_checked_at = datetime.now(UTC)
    package.failure_count = 0
    package.check_interval_seconds = _next_interval_for_status(result.status)
    package.next_check_at = (
        None
        if result.status == PackageStatus.DELIVERED
        else datetime.now(UTC) + timedelta(seconds=package.check_interval_seconds)
    )

    existing_keys = {(event.occurred_at, event.description) for event in package.events}
    for event_dto in result.events:
        key = (event_dto.occurred_at, event_dto.description)
        if key in existing_keys:
            continue
        package.events.append(
            TrackingEvent(
                provider_id=package.provider_id,
                occurred_at=event_dto.occurred_at,
                status=event_dto.status,
                location=event_dto.location,
                description=event_dto.description,
                raw_payload=event_dto.raw,
            )
        )
        existing_keys.add(key)


def reset_for_retarget(package: Package) -> None:
    """Clear tracking history and status after the tracking number, carrier, or provider
    changed -- the accumulated events describe a shipment this package no longer represents.

    ``next_check_at`` is set to now so the next poll (or Celery beat tick) picks it up promptly
    instead of waiting a full default interval.
    """
    package.events.clear()
    package.status = PackageStatus.CREATED
    package.failure_count = 0
    package.check_interval_seconds = DEFAULT_CHECK_INTERVAL_SECONDS
    package.last_checked_at = None
    package.next_check_at = datetime.now(UTC)


def record_fetch_failure(package: Package) -> None:
    """Back off exponentially (capped) after a failed fetch, without touching package.status."""
    package.failure_count += 1
    package.check_interval_seconds = min(
        package.check_interval_seconds * 2, MAX_CHECK_INTERVAL_SECONDS
    )
    package.next_check_at = datetime.now(UTC) + timedelta(seconds=package.check_interval_seconds)
