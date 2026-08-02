import uuid
from datetime import UTC, datetime

from app.models.enums import PackageStatus
from app.models.package import DEFAULT_CHECK_INTERVAL_SECONDS, MAX_CHECK_INTERVAL_SECONDS, Package
from app.providers.base import TrackingEventDTO, TrackingResult
from app.services.tracking import apply_tracking_result, record_fetch_failure


def _bare_package(**overrides: object) -> Package:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "tracking_number": "AB123456789IT",
        "carrier_id": uuid.uuid4(),
        "provider_id": uuid.uuid4(),
        "status": PackageStatus.CREATED,
        "check_interval_seconds": DEFAULT_CHECK_INTERVAL_SECONDS,
        "failure_count": 0,
    }
    defaults.update(overrides)
    return Package(**defaults)  # type: ignore[arg-type]


def test_apply_tracking_result_updates_status_and_appends_new_events() -> None:
    package = _bare_package()
    result = TrackingResult(
        status=PackageStatus.IN_TRANSIT,
        events=[
            TrackingEventDTO(
                occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
                status=PackageStatus.IN_TRANSIT,
                description="Picked up",
            )
        ],
    )

    apply_tracking_result(package, result)

    assert package.status is PackageStatus.IN_TRANSIT
    assert package.failure_count == 0
    assert package.last_checked_at is not None
    assert len(package.events) == 1
    assert package.next_check_at is not None


def test_apply_tracking_result_deduplicates_events_already_present() -> None:
    package = _bare_package()
    occurred_at = datetime(2026, 1, 1, tzinfo=UTC)
    first = TrackingResult(
        status=PackageStatus.IN_TRANSIT,
        events=[
            TrackingEventDTO(
                occurred_at=occurred_at, status=PackageStatus.IN_TRANSIT, description="Picked up"
            )
        ],
    )
    apply_tracking_result(package, first)

    second = TrackingResult(
        status=PackageStatus.IN_TRANSIT,
        events=[
            TrackingEventDTO(
                occurred_at=occurred_at, status=PackageStatus.IN_TRANSIT, description="Picked up"
            ),
            TrackingEventDTO(
                occurred_at=datetime(2026, 1, 2, tzinfo=UTC),
                status=PackageStatus.OUT_FOR_DELIVERY,
                description="Out for delivery",
            ),
        ],
    )
    apply_tracking_result(package, second)

    assert len(package.events) == 2


def test_apply_tracking_result_stops_scheduling_once_delivered() -> None:
    package = _bare_package()
    result = TrackingResult(status=PackageStatus.DELIVERED, events=[])

    apply_tracking_result(package, result)

    assert package.next_check_at is None


def test_apply_tracking_result_polls_faster_when_out_for_delivery() -> None:
    package = _bare_package()
    result = TrackingResult(status=PackageStatus.OUT_FOR_DELIVERY, events=[])

    apply_tracking_result(package, result)

    assert package.check_interval_seconds < DEFAULT_CHECK_INTERVAL_SECONDS


def test_record_fetch_failure_backs_off_exponentially_up_to_a_cap() -> None:
    package = _bare_package(check_interval_seconds=MAX_CHECK_INTERVAL_SECONDS // 2 + 100)

    record_fetch_failure(package)

    assert package.failure_count == 1
    assert package.check_interval_seconds <= MAX_CHECK_INTERVAL_SECONDS
    assert package.next_check_at is not None
