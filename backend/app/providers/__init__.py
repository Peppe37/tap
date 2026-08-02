"""Tracking provider plugin package.

Every concrete provider module is imported here explicitly so that its
``@register_provider``-decorated class registers itself on import. This is a deliberate choice
over dynamic plugin discovery (entry points / directory scanning): it keeps the set of active
providers explicit, type-checkable, and easy to trace when debugging.

To add a new provider, see docs/ADDING_A_PROVIDER.md.
"""

from app.providers.generic_aggregator.provider import SeventeenTrackProvider
from app.providers.inpost.provider import InPostProvider
from app.providers.poste_it.provider import PosteItalianeProvider
from app.providers.registry import provider_registry

__all__ = ["InPostProvider", "PosteItalianeProvider", "SeventeenTrackProvider", "provider_registry"]
