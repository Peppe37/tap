# Architecture

## Overview

```
frontend (React/Vite)  --->  backend (FastAPI)  --->  PostgreSQL
                                    |
                                    +--> Redis  <---  Celery worker + beat
                                    |
                                    +--> tracking providers (InPost, Poste Italiane, 17TRACK, ...)
```

The backend is the only thing that talks to PostgreSQL, Redis, or any external tracking provider.
The frontend only ever talks to the backend's REST API.

## Data model

- **User** — an account on this instance. `is_admin` gates user management endpoints.
- **Carrier** — a shipping company (BRT, GLS, Poste Italiane, InPost, ...). Seeded from
  `backend/app/seed/carriers.yaml`.
- **Shop** — a marketplace/retailer (AliExpress, Amazon, ...), used only to suggest likely
  carriers in the add-tracker UI. Seeded from `backend/app/seed/shops.yaml`; the suggestions
  themselves come from `ShopCarrierHint` rows seeded from `shop_carrier_hints.yaml`.
- **Provider** — a concrete way of fetching tracking data for one or more carriers: an official
  API, a scraper, or a third-party aggregator. Seeded from `backend/app/seed/providers.yaml`,
  which is also where a provider's `setup_guide` (rendered by the frontend's guided "Connections"
  screen) lives.
- **ProviderCarrierSupport** / **ProviderCarrierExclusion** — which carriers a provider covers.
  A provider with `supports_all_carriers=True` (an aggregator) needs no rows here at all; carriers
  it explicitly does *not* cover go in `ProviderCarrierExclusion` instead. A provider that only
  covers a handful of carriers (an official API or scraper) lists them explicitly in
  `ProviderCarrierSupport`. The query for "which providers can track carrier X" is a union of
  both cases — see `list_providers_for_carrier` in `backend/app/api/routers/carriers.py`.
- **Package** — a tracked shipment: the tracking number, the chosen carrier/provider/shop, the
  normalized `status`, and the polling schedule (`next_check_at`, `check_interval_seconds`,
  `failure_count`).
- **TrackingEvent** — one status update in a package's history, deduplicated on
  `(occurred_at, description)` so re-fetching the same data never creates duplicates.
- **UserProviderCredential** — a user's own credentials for a provider that needs them (e.g. an
  aggregator API key), encrypted at rest with a server-side Fernet key
  (`TAP_CREDENTIAL_ENCRYPTION_KEY`) and never returned decrypted by the API.

## The provider plugin system

Every concrete way of fetching tracking data implements `TrackingProvider`
(`backend/app/providers/base.py`):

```python
class TrackingProvider(ABC):
    code: ClassVar[str]
    kind: ClassVar[ProviderKind]                       # official_api | scraper | aggregator
    supports_all_carriers: ClassVar[bool] = False
    supported_carrier_codes: ClassVar[frozenset[str]] = frozenset()
    requires_credentials: ClassVar[bool] = False

    async def fetch(self, tracking_number, carrier_code, credentials) -> TrackingResult: ...
    async def test_credentials(self, credentials) -> bool: ...   # only if requires_credentials
```

Each provider lives in its own package under `backend/app/providers/<code>/` and registers itself
with a class decorator on import:

```python
@register_provider
class InPostProvider(TrackingProvider):
    code = "inpost_official"
    ...
```

`backend/app/providers/__init__.py` imports every provider module explicitly — a deliberate
choice over dynamic plugin discovery (scanning directories, entry points): the set of active
providers stays explicit, type-checkable, and easy to trace. See
[ADDING_A_PROVIDER.md](ADDING_A_PROVIDER.md) for the full walkthrough of adding one.

Three real providers ship today, one per `ProviderKind`:

| Provider | Kind | Carrier(s) | Credentials |
|---|---|---|---|
| `inpost_official` | `official_api` | InPost | none |
| `poste_it_scraper` | `scraper` | Poste Italiane | none |
| `aggregator_17track` | `aggregator` | any (fallback) | user's own 17TRACK API key |

## Request flow: adding and refreshing a package

1. `GET /api/shops` → the add-tracker wizard shows shop options and, once one is picked, the
   carriers that shop's `ShopCarrierHint` rows suggest (purely a UX hint, never enforced).
2. `GET /api/carriers/{code}/providers` → once a carrier is picked, the wizard lists every
   provider that covers it, so the user can choose official API vs. scraper vs. aggregator.
3. `POST /api/packages` → validates the chosen provider actually covers the chosen carrier
   (`_provider_supports_carrier` in `backend/app/api/routers/packages.py`) before creating the row.
4. `POST /api/packages/{id}/refresh` → looks up the provider implementation in the registry,
   loads the user's decrypted credentials if the provider needs them, calls `fetch()`, and applies
   the result via `apply_tracking_result` (`backend/app/services/tracking.py`) — the same function
   the Celery task uses, so on-demand and scheduled refreshes behave identically.

Provider errors (`backend/app/providers/base.py`) map to HTTP statuses through a single exception
handler (`backend/app/api/errors.py`) rather than per-endpoint try/except:
`ProviderInvalidTrackingNumberError` → 404, `ProviderNotConfiguredError` → 409,
`ProviderRateLimitedError` → 429, `ProviderAuthenticationError` → 424, anything else → 502.

## Scheduled polling (Celery)

`backend/app/workers/tasks.py` has two tasks:

- `enqueue_due_packages` — runs every 5 minutes (see the beat schedule in
  `backend/app/core/celery_app.py`). Selects packages whose `next_check_at` has passed (or is
  still `NULL`, i.e. never checked) and dispatches `check_package_status` for each.
- `check_package_status` — does the actual fetch for one package, then:
  - on success, calls `apply_tracking_result`, which speeds up polling to every 5 minutes while a
    package is `out_for_delivery` and stops polling entirely once it's `delivered`;
  - on a permanent error (invalid tracking number, bad/missing credentials), calls
    `record_fetch_failure` (exponential backoff, capped at 24h) and does *not* retry;
  - on a transient error or a rate limit, calls `record_fetch_failure` and re-raises, so Celery's
    `autoretry_for` handles the retry with exponential backoff.

Per-provider request-rate limiting (respecting, say, an aggregator's free-tier quota) is enforced
*inside* `check_package_status` itself, via a Redis fixed-window counter keyed by provider code
and configured through `Provider.config["max_requests_per_minute"]` — not via dedicated Celery
queues. This keeps the provider plugin system the one place that needs to know about a given
provider's limits, and means a single worker process handles every provider regardless of how
many are installed.

## Guided onboarding

Two flows exist specifically because this is meant to be self-hosted by people who are not
necessarily the ones who built it:

- **First-run setup**: `GET /api/auth/setup-status` reports whether any `User` exists yet. If not,
  the frontend shows a "create the admin account" screen instead of a login form
  (`frontend/src/features/setup/FirstRunSetup.tsx`). `POST /api/auth/setup` only succeeds once,
  ever, per instance.
- **Guided connections**: for providers with `requires_credentials=True`, `Provider.setup_guide`
  (seeded JSON: an intro, numbered steps with optional links, and the credential fields to
  collect) drives `frontend/src/features/settings/ConnectionGuideCard.tsx`, which renders the
  instructions, lets the user test their credentials against the real provider
  (`POST /api/providers/{code}/test-credential`, backed by `TrackingProvider.test_credentials`)
  before saving anything, and shows whether a connection is currently configured.
