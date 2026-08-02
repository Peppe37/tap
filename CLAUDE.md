# CLAUDE.md

Instructions for Claude Code (and any other agent) working in this repository.

## What this project is

tap ("Track All Parcels") is an open source, self-hosted, multi-carrier package tracking platform.
Backend: Python/FastAPI + SQLAlchemy 2.0 async + PostgreSQL + Celery/Redis. Frontend: React +
TypeScript + Vite + TanStack Query + Tailwind CSS. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
for the full design and [docs/ADDING_A_PROVIDER.md](docs/ADDING_A_PROVIDER.md) before touching a
carrier integration.

## Non-negotiable quality bar

This is meant to be a genuinely complete, enterprise-quality open source product, not a prototype.
Concretely:

- **Lint, type-check, and test everything.** Backend: `ruff check .`, `ruff format --check .`,
  `mypy app`, `pytest --cov=app`. Frontend: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`,
  `pnpm test`, `pnpm build`. All of this runs in CI (`.github/workflows/ci.yml`); run it locally
  before considering anything done.
- **No emoji, anywhere** — in code, commit messages, docs, or UI. The frontend uses `lucide-react`
  icons exclusively for anything that needs a visual marker.
- **No filler content.** Every carrier, shop, and provider in the seed data
  (`backend/app/seed/*.yaml`) is real. Every provider adapter talks to a real, verified endpoint.
  Don't add placeholder carriers/shops or invented API shapes to "look complete."
- **Never invent third-party API/endpoint details.** Before writing or modifying a
  `TrackingProvider` implementation, verify the real endpoint, request/response shape, and status
  vocabulary (via direct HTTP requests, official docs, or existing verified code) — do not guess
  field names or status enums. Getting this wrong doesn't just fail a test; it can register bad
  data with a real third-party account (this has happened before in this project).
- **Respect third-party rate limits.** In particular, 17TRACK (`aggregator_17track`) is a real
  external account with its own quota — do not hammer it with rapid sequential test calls. Prefer
  going through this app's own `/packages/{id}/refresh` endpoint over calling 17TRACK's API
  directly when verifying behavior by hand.
- **No backwards-compatibility shims, no dead code.** If something is unused, delete it. Don't
  rename instead of removing, don't leave `# removed` comments.

## Commit conventions

Every commit message follows [Conventional Commits](https://www.conventionalcommits.org/):
`<type>(<scope>): <description>` — see [CONTRIBUTING.md](CONTRIBUTING.md#conventional-commits) for
the exact rules. This is enforced (pre-commit's `conventional-pre-commit` hook, and CI's
`commitlint` job on pull requests) because merges to `main` trigger automated releases via
semantic-release (`.releaserc.json`, `.github/workflows/release.yml`) based on these prefixes.

When asked to commit a batch of work, split it into multiple logically-scoped commits rather than
one large commit, unless told otherwise. Group by capability/layer (e.g. "add the provider plugin
system" as one commit, "add the package API" as another), not by chronology of how the work
happened to be typed.

## Security posture

- `pip-audit`, `bandit`, `pnpm audit`, and `gitleaks` all run in CI (`.github/workflows/security.yml`)
  plus CodeQL (`codeql.yml`). Treat a new advisory as something to actually fix, not silence, unless
  you can show the vulnerable code path is genuinely unreachable in how this app uses the
  dependency — and if you do suppress one, document *why* right next to the suppression (see
  `frontend/pnpm-workspace.yaml`'s `auditConfig.ignoreGhsas` comment for the expected level of
  detail), not just that you did.
- Provider credentials are encrypted at rest with a Fernet key (`app/core/encryption.py`,
  `TAP_CREDENTIAL_ENCRYPTION_KEY`). Never log or print a decrypted credential; if you need to
  inspect one for debugging, check length/presence only.
- `gitleaks` (in `security.yml`) scans full git history on every run, so a known-safe test/CI
  fixture value (e.g. the fixed `TAP_CREDENTIAL_ENCRYPTION_KEY` used in `ci.yml` and
  `tests/integration/conftest.py`) gets flagged once per historical commit that touches it, not
  just once. Suppress each with a fingerprint (`<commit>:<file>:<rule-id>:<line>`) in
  `.gitleaksignore`, plus an inline `# gitleaks:allow` comment on the line itself where the
  line-length limit allows it (YAML has no such limit; Python's 100-char `ruff` limit sometimes
  doesn't). If you edit a line that already has a `.gitleaksignore` entry, the entry's commit hash
  goes stale — add a new fingerprint for the new commit rather than editing the old one.
- `.claude/` is gitignored on purpose — it can accumulate session tokens via the permission
  allowlist. Never remove it from `.gitignore`.
- Double-check `.gitignore` patterns against both `backend/` and `frontend/` before trusting them:
  the generic Python template this repo started from previously had an unscoped `lib/` entry that
  silently matched (and excluded from git) `frontend/src/lib/`, a real source directory.

## Provider plugin system

New carrier integrations live under `backend/app/providers/<name>/` and self-register with
`@register_provider` (see `backend/app/providers/registry.py`). They're imported explicitly in
`app/providers/__init__.py` — there is no dynamic plugin discovery, by design. A provider that
needs user credentials must implement `test_credentials()` and ship a `setup_guide` (seeded via
`backend/app/seed/providers.yaml`) so it shows up correctly in the frontend's guided Connections
flow. Follow [docs/ADDING_A_PROVIDER.md](docs/ADDING_A_PROVIDER.md) step by step.

## Documentation

- `docs/` is published as a MkDocs site (`mkdocs.yml`) to GitHub Pages on every push to `main` that
  touches it. Run `mkdocs build --strict` before considering a docs change done — it treats broken
  internal links as errors.
- `docs/contributing.md` and `docs/changelog.md` snippet-include the root `CONTRIBUTING.md` /
  `CHANGELOG.md` (via `pymdownx.snippets`) rather than duplicating them. If you add a link inside
  `CONTRIBUTING.md`, use an absolute `https://github.com/Peppe37/tap/...` URL rather than a
  relative repo path — a relative path that resolves correctly from the repo root (where GitHub
  renders `CONTRIBUTING.md`) will not resolve from `docs/contributing.md`'s position in the
  MkDocs tree, and vice versa. `CHANGELOG.md` is generated by semantic-release; never hand-edit it.

## Docker images and the update check

- `.github/workflows/docker-publish.yml` publishes multi-arch images to GHCR
  (`ghcr.io/peppe37/tap-{backend,frontend}`): an `edge` tag on every push to `main`, versioned
  tags + `latest` on each GitHub Release (triggered by the native `release: published` event
  `@semantic-release/github` fires — not chained off `release.yml` directly). `backend/Dockerfile`
  bakes the release tag into the image (`APP_VERSION` build arg → `TAP_APP_VERSION` env var);
  anything built outside that pipeline (local dev) defaults to `"dev"`.
- `GET /api/system/update-status` (`app/services/update_check.py`) compares that baked-in version
  against the latest GitHub Release, admin-only, cached in Redis for 6h. A `"dev"` version never
  reports an update (it doesn't parse as semver, so there's nothing meaningful to compare) — don't
  "fix" that by making it always compare; local dev builds having no versioned identity is correct.
