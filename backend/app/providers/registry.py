"""In-process registry mapping provider codes to their singleton implementation instance."""

from app.providers.base import TrackingProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, TrackingProvider] = {}

    def register(self, provider: TrackingProvider) -> None:
        if provider.code in self._providers:
            raise ValueError(f"provider code {provider.code!r} is already registered")
        self._providers[provider.code] = provider

    def get(self, code: str) -> TrackingProvider:
        try:
            return self._providers[code]
        except KeyError as exc:
            raise KeyError(f"no provider registered with code {code!r}") from exc

    def all(self) -> list[TrackingProvider]:
        return list(self._providers.values())

    def for_carrier(self, carrier_code: str) -> list[TrackingProvider]:
        return [p for p in self._providers.values() if p.supports_carrier(carrier_code)]


provider_registry = ProviderRegistry()


def register_provider[T: TrackingProvider](cls: type[T]) -> type[T]:
    """Class decorator: instantiate a provider and add it to the global registry on import."""
    provider_registry.register(cls())
    return cls
