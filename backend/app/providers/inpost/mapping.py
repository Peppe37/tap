"""Mapping from InPost ShipX status codes to the platform's normalized status.

Source: InPost ShipX API developer documentation, "Statuses" reference
(https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/18153478), current as of the
adapter's implementation date. If InPost adds a new status not listed here, it falls back to
UNKNOWN rather than guessing.
"""

from app.models.enums import PackageStatus

STATUS_MAP: dict[str, PackageStatus] = {
    "created": PackageStatus.CREATED,
    "offers_prepared": PackageStatus.CREATED,
    "offer_selected": PackageStatus.CREATED,
    "confirmed": PackageStatus.CREATED,
    "ready_to_pickup_from_pok": PackageStatus.IN_TRANSIT,
    "dispatched_by_sender_to_pok": PackageStatus.IN_TRANSIT,
    "dispatched_by_sender": PackageStatus.IN_TRANSIT,
    "collected_from_sender": PackageStatus.IN_TRANSIT,
    "taken_by_courier": PackageStatus.IN_TRANSIT,
    "adopted_at_source_branch": PackageStatus.IN_TRANSIT,
    "sent_from_source_branch": PackageStatus.IN_TRANSIT,
    "adopted_at_sorting_center": PackageStatus.IN_TRANSIT,
    "readdressed": PackageStatus.IN_TRANSIT,
    "ready_to_pickup": PackageStatus.IN_TRANSIT,
    "ready_to_pickup_from_branch": PackageStatus.IN_TRANSIT,
    "pickup_reminder_sent": PackageStatus.IN_TRANSIT,
    "pickup_reminder_sent_address": PackageStatus.IN_TRANSIT,
    "stack_in_customer_service_point": PackageStatus.IN_TRANSIT,
    "stack_in_box_machine": PackageStatus.IN_TRANSIT,
    "unstack_from_customer_service_point": PackageStatus.IN_TRANSIT,
    "unstack_from_box_machine": PackageStatus.IN_TRANSIT,
    "courier_avizo_in_customer_service_point": PackageStatus.IN_TRANSIT,
    "taken_by_courier_from_customer_service_point": PackageStatus.IN_TRANSIT,
    "redirect_to_box": PackageStatus.IN_TRANSIT,
    "delay_in_delivery": PackageStatus.IN_TRANSIT,
    "avizo": PackageStatus.IN_TRANSIT,
    "oversized": PackageStatus.IN_TRANSIT,
    "out_for_delivery": PackageStatus.OUT_FOR_DELIVERY,
    "out_for_delivery_to_address": PackageStatus.OUT_FOR_DELIVERY,
    "delivered": PackageStatus.DELIVERED,
    "rejected_by_receiver": PackageStatus.EXCEPTION,
    "undelivered": PackageStatus.EXCEPTION,
    "undelivered_wrong_address": PackageStatus.EXCEPTION,
    "undelivered_cod_cash_receiver": PackageStatus.EXCEPTION,
    "returned_to_sender": PackageStatus.EXCEPTION,
    "canceled": PackageStatus.EXCEPTION,
    "canceled_redirect_to_box": PackageStatus.EXCEPTION,
    "claimed": PackageStatus.EXCEPTION,
    "pickup_time_expired": PackageStatus.EXCEPTION,
    "stack_parcel_pickup_time_expired": PackageStatus.EXCEPTION,
    "stack_parcel_in_box_machine_pickup_time_expired": PackageStatus.EXCEPTION,
}
