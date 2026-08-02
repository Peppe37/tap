# Self-hosting

tap ships as a Docker Compose stack: PostgreSQL, Redis, the FastAPI backend, a Celery worker and
beat scheduler for automatic polling, and an nginx-served frontend that reverse-proxies `/api` to
the backend. There is nothing else to install.

## Prerequisites

- Docker Engine and the Docker Compose plugin (`docker compose version`).
- A place to run it with the ports `8080` (frontend) and `8000` (backend API) free, or edit
  `docker-compose.yml` to change them.

## Quick start

```bash
git clone https://github.com/Peppe37/tap.git
cd tap
cp .env.example .env
```

Edit `.env` and fill in the secrets `.env.example` leaves blank:

```bash
# JWT signing key for access/refresh tokens
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Fernet key used to encrypt provider credentials (e.g. an aggregator API key) at rest
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

(No Python locally? Run either command through Docker instead:
`docker run --rm python:3.12-slim python3 -c "..."`.)

Also change `POSTGRES_PASSWORD` from the placeholder. Then:

```bash
docker compose up --build
```

- Frontend: <http://localhost:8080>
- Backend API + interactive docs: <http://localhost:8000/docs>

The backend container runs database migrations (`alembic upgrade head`) and seeds the built-in
carrier/shop/provider catalogue on every startup, so a fresh instance is ready to use as soon as
the containers report healthy.

## First run

Opening the frontend for the first time shows a **"Create the administrator account"** screen
instead of a login form — this is a one-time bootstrap step (the backend exposes
`GET /auth/setup-status` to detect that no user exists yet). Once created, every further user is
added from inside the app by an existing account; there is no public sign-up.

## Guided connections

Carriers can be tracked through more than one method: an official carrier API, a maintained
scraper, or a third-party aggregator. Methods that need a personal API key (aggregators, mainly)
show up under **Settings → Connections** with:

- step-by-step instructions for obtaining the credential from that provider's own site,
- the exact fields to fill in,
- a "test connection" check that calls the provider before anything is saved.

Nothing is stored until the test succeeds, and credentials are encrypted at rest with the Fernet
key you generated above (`TAP_CREDENTIAL_ENCRYPTION_KEY`) — losing that key makes stored
credentials unrecoverable, so back it up along with the database.

## Environment variables

All of these live in `.env` at the repo root, read by `docker-compose.yml`:

| Variable | Purpose |
| --- | --- |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Credentials for the bundled PostgreSQL container. |
| `TAP_ENVIRONMENT` | `production` by default; informational, used in a few log/error messages. |
| `TAP_DATABASE_URL` | SQLAlchemy async URL the backend uses to reach Postgres. |
| `TAP_REDIS_URL` | Redis URL shared by Celery (broker/result backend) and the local rate limiter. |
| `TAP_JWT_SECRET_KEY` | Signs access/refresh tokens. Rotating it invalidates every existing session. |
| `TAP_CREDENTIAL_ENCRYPTION_KEY` | Fernet key encrypting stored provider credentials. |
| `TAP_CORS_ORIGINS` | JSON array of allowed origins for the API (only matters if you serve the frontend from a different origin than the default nginx proxy). |
| `VITE_API_BASE_URL` | Base path the frontend calls; left as `/api` unless you split frontend/backend across origins. |

## Updating

```bash
git pull
docker compose up --build
```

Migrations run automatically on backend startup; there's no separate migration step to remember.

## Backups

Everything that matters lives in the `postgres-data` named volume (packages, tracking history,
users, encrypted credentials) plus the two secrets in `.env`
(`TAP_JWT_SECRET_KEY`, `TAP_CREDENTIAL_ENCRYPTION_KEY` — without the encryption key, backed-up
credentials can't be decrypted even if the database is restored). A simple `pg_dump` against the
`postgres` service, together with a copy of `.env`, is enough to restore an instance elsewhere.

## Security scanning

Every push and pull request runs three separate GitHub Actions workflows on top of linting and
tests: `security.yml` (`pip-audit` and `bandit` for the backend, `pnpm audit` for the frontend,
a `gitleaks` secret scan across the whole repository), `codeql.yml` (static analysis for Python
and JavaScript/TypeScript), and dependency updates flow through the same `pnpm audit` /
`pip-audit` gate before merge. Two frontend advisories are currently accepted as not applicable
rather than fixed — see the comment above `auditConfig` in `frontend/pnpm-workspace.yaml` for the
reasoning behind each one.

## Local development

See [Contributing](contributing.md) for running the backend and frontend outside Docker.
