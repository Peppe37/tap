"""Common interface every tracking provider adapter must implement."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

from app.models.enums import PackageStatus, ProviderKind


class ProviderError(Exception):
    """Base class for all provider-raised errors."""


class ProviderTransientError(ProviderError):
    """A retryable failure: network timeout, 5xx, temporary provider outage."""


class ProviderRateLimitedError(ProviderTransientError):
    """The provider (or our own quota with it) is rate-limited right now."""


class ProviderInvalidTrackingNumberError(ProviderError):
    """The tracking number is not recognised by the provider for the given carrier."""


class ProviderAuthenticationError(ProviderError):
    """The stored/supplied credentials were rejected by the provider."""


class ProviderNotConfiguredError(ProviderError):
    """The provider requires credentials that have not been supplied for this user."""


@dataclass(frozen=True, slots=True)
class TrackingEventDTO:
    occurred_at: datetime
    status: PackageStatus
    description: str
    location: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrackingResult:
    status: PackageStatus
    events: list[TrackingEventDTO]
    raw: dict[str, Any] = field(default_factory=dict)


class TrackingProvider(ABC):
    """Base class for a concrete way of fetching tracking data for one or more carriers.

    Subclasses declare their identity and capabilities as class attributes and implement
    ``fetch`` (and, if ``requires_credentials`` is True, ``test_credentials``).
    """

    code: ClassVar[str]
    display_name: ClassVar[str]
    kind: ClassVar[ProviderKind]
    supports_all_carriers: ClassVar[bool] = False
    supported_carrier_codes: ClassVar[frozenset[str]] = frozenset()
    requires_credentials: ClassVar[bool] = False

    @abstractmethod
    async def fetch(
        self,
        tracking_number: str,
        carrier_code: str,
        credentials: dict[str, str] | None,
        extra_params: dict[str, str] | None = None,
    ) -> TrackingResult:
        """Fetch the current tracking status and event history for a shipment.

        ``extra_params`` carries per-package details a provider may need beyond the tracking
        number itself -- e.g. some carriers require the destination postal code when tracked
        through an aggregator. Most providers ignore it entirely.

        Raises a subclass of ``ProviderError`` on any failure; never returns partial/invalid
        data silently.
        """

    async def test_credentials(self, credentials: dict[str, str]) -> bool:
        """Validate a set of user-supplied credentials without persisting anything.

        Only relevant when ``requires_credentials`` is True. The default implementation raises
        ``NotImplementedError`` so that providers requiring credentials are forced to implement
        a real check used by the "test connection" step of the guided setup UI.
        """
        raise NotImplementedError(f"{self.code} does not implement test_credentials")

    def supports_carrier(self, carrier_code: str) -> bool:
        if self.supports_all_carriers:
            return True
        return carrier_code in self.supported_carrier_codes
