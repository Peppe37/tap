# Adding a tracking provider

A "provider" is one concrete way of fetching tracking data for one or more carriers: an official
carrier API, a scraper of an unofficial-but-stable endpoint, or a third-party aggregator. Read
[ARCHITECTURE.md](ARCHITECTURE.md) first for how providers fit into the rest of the system.

## Before writing code: verify the endpoint

Do not guess or invent an endpoint, request shape, or status enum. Before implementing anything:

1. Look for the carrier's official API documentation. If one exists and is usable without a
   business account, that's an `official_api` provider.
2. If not, look for how the carrier's own public tracking *website* fetches data — browser
   dev tools' network tab, or community projects (GitHub, Home Assistant integrations, etc.) that
   already reverse-engineered it. That's a `scraper` provider. Note where you found it; unofficial
   endpoints can change or start blocking non-browser clients without notice, so the next person
   maintaining this adapter needs to know where to look when it breaks.
3. Record the real request/response shape (field names, status codes/strings) you found. If you
   can't confirm something, don't encode it as if you had — map it to `PackageStatus.UNKNOWN` and
   say so in a comment, rather than inventing a status value.

## Steps

1. **Create the package**: `backend/app/providers/<your_code>/` with `__init__.py`,
   `provider.py`, and (if the carrier has a real status enum) `mapping.py`. Look at
   `backend/app/providers/inpost/` (exact status codes, `official_api`) or
   `backend/app/providers/poste_it/` (no stable enum, free-text keyword classification via
   `backend/app/providers/status.py`'s `map_by_keywords`) as templates depending on which
   situation you're in.

2. **Implement the class**, subclassing `TrackingProvider` (`backend/app/providers/base.py`):

   ```python
   @register_provider
   class YourCarrierProvider(TrackingProvider):
       code = "your_carrier_official"        # stable, never rename once shipped
       display_name = "Your Carrier"
       kind = ProviderKind.OFFICIAL_API        # or SCRAPER / AGGREGATOR
       supported_carrier_codes = frozenset({"your_carrier"})
       requires_credentials = False

       async def fetch(self, tracking_number, carrier_code, credentials) -> TrackingResult:
           ...
   ```

   Raise the specific exception from `backend/app/providers/base.py` that matches the failure —
   `ProviderInvalidTrackingNumberError`, `ProviderRateLimitedError`, `ProviderTransientError`,
   `ProviderAuthenticationError`, `ProviderNotConfiguredError` — rather than a generic exception;
   the API layer maps these to specific HTTP statuses automatically
   (`backend/app/api/errors.py`), and the Celery poller treats "permanent" vs. "transient" errors
   differently (see [ARCHITECTURE.md](ARCHITECTURE.md#scheduled-polling-celery)).

   If `requires_credentials = True`, also implement `test_credentials()` with a cheap,
   non-destructive call that validates the credentials without registering/tracking anything
   real — this backs the frontend's "test connection" button.

3. **Register it** in `backend/app/providers/__init__.py`: add the explicit import (this is what
   triggers `@register_provider`). Providers are not auto-discovered on purpose — see
   [ARCHITECTURE.md](ARCHITECTURE.md#the-provider-plugin-system).

4. **Seed it**: add an entry to `backend/app/seed/providers.yaml` —

   ```yaml
   - code: your_carrier_official   # must match TrackingProvider.code exactly
     display_name: Your Carrier
     kind: official_api
     requires_credentials: false
     supports_all_carriers: false
     carriers: [your_carrier]      # carrier codes this provider covers
   ```

   If the carrier itself is new, add it to `backend/app/seed/carriers.yaml` too. If
   `requires_credentials: true`, add a `setup_guide` block (see `aggregator_17track`'s entry for
   the shape: `intro`, `steps` with optional `link`, `fields` with `key`/`label`/`type`/
   `required`/`help_text`) — this is what renders in the frontend's guided Connections screen.

5. **Write unit tests** under `backend/tests/unit/providers/test_<your_code>.py`, mocking HTTP
   with `respx` against fixtures in `backend/tests/unit/fixtures/providers/<your_code>/` built
   from real responses you captured in step 0. Cover at least: a successful multi-event response,
   an unknown/invalid tracking number, and (if applicable) a rate-limit response. See
   `backend/tests/unit/providers/test_inpost.py` for the pattern.

6. **Run the checks**: `ruff check . && mypy app && pytest` from `backend/`. Then run the seed
   loader against a real database (`python -m app.seed.loader`) and confirm
   `GET /api/carriers/<code>/providers` lists your new provider.

## A note on unofficial endpoints

Scraper-kind providers (like `poste_it_scraper`) call endpoints that aren't part of a documented,
supported API. That's an accepted trade-off for carriers with no real alternative, not something
to hide: say so in the class docstring, link to where you confirmed the request/response shape,
and keep the implementation defensive (explicit status-code handling, no silent assumptions about
fields that might not be present).
