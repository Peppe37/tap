# tap — Track All Parcels

An open source, self-hosted platform for tracking packages across multiple carriers and
marketplaces — InPost, Poste Italiane, BRT, GLS, and any carrier covered by a third-party
aggregator — from one dashboard, on your own infrastructure.

Full documentation: <https://Peppe37.github.io/tap/>.

## Why

Every carrier has its own tracking page, its own quirks, and its own coverage gaps. tap gives you
one place to add a tracking number, tell it where you bought the item and who is shipping it, and
let it pick the best available way to follow the shipment: an official carrier API where one
exists, a maintained scraper where it doesn't, or a third-party aggregator as a fallback.

## Features

- **Multi-user**: designed for a household, a team, or any group of self-hosters sharing one
  instance, with per-user data isolation and an admin role.
- **Pluggable tracking providers**: a carrier can be tracked through more than one method (official
  API, scraper, aggregator); you choose which one to use per package. See
  [docs/ADDING_A_PROVIDER.md](docs/ADDING_A_PROVIDER.md) to add support for a new carrier.
- **Guided onboarding**: first boot walks you through creating the admin account; providers that
  need a personal API key (e.g. an aggregator) come with step-by-step setup instructions and a
  "test connection" check before you save anything.
- **Automatic polling**: a Celery worker refreshes active packages on a schedule that speeds up
  while a package is out for delivery and stops once it's delivered, with per-provider rate
  limiting and exponential backoff on failures.
- **On-demand refresh**: don't want to wait for the next scheduled check? Refresh any package from
  its detail page.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full picture. In short:

- **Backend**: Python, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Celery + Redis for scheduled
  polling.
- **Frontend**: React, TypeScript, Vite, TanStack Query, Tailwind CSS.
- **Tracking providers**: a small plugin system (`backend/app/providers/`) — each carrier can be
  backed by one or more provider implementations (official API, scraper, aggregator).

## Running it

### With Docker Compose (recommended)

```bash
cp .env.example .env
# Fill in TAP_JWT_SECRET_KEY and TAP_CREDENTIAL_ENCRYPTION_KEY (instructions are in .env.example)
docker compose up --build
```

- Frontend: <http://localhost:8080>
- Backend API + docs: <http://localhost:8000/docs>

The backend container runs database migrations and seeds the carrier/shop/provider catalogue
automatically on startup — there is nothing else to set up.

Prefer not to build locally? Pre-built images are published to GitHub Container Registry on every
release (`ghcr.io/peppe37/tap-backend`, `ghcr.io/peppe37/tap-frontend`, both multi-arch:
amd64/arm64) — see [Self-hosting](https://Peppe37.github.io/tap/self-hosting/#using-pre-built-images)
for the one-line `docker compose` override that uses them instead.

### Local development

Backend (Python 3.12, PostgreSQL, Redis required):

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in secrets, point TAP_DATABASE_URL at your local Postgres
alembic upgrade head
python -m app.seed.loader
uvicorn app.main:app --reload
```

Run the test suite with `pytest`, lint with `ruff check .`, type-check with `mypy app`.

Frontend (Node 22+, pnpm):

```bash
cd frontend
pnpm install
pnpm dev
```

Run tests with `pnpm test`, lint with `pnpm lint`, type-check with `pnpm typecheck`.

Async polling (optional for local dev — the on-demand refresh button works without it):

```bash
celery -A app.core.celery_app:celery_app worker --loglevel=info
celery -A app.core.celery_app:celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Adding a new carrier or tracking method? Start with
[docs/ADDING_A_PROVIDER.md](docs/ADDING_A_PROVIDER.md).

## License

MIT — see [LICENSE](LICENSE).
