# Security Policy

## Supported versions

tap is a single, continuously-released project (no parallel maintained branches) --
security fixes land on the latest release. If you're running an older version, upgrading is the
fix; see [Self-hosting: Using pre-built images](https://Peppe37.github.io/tap/self-hosting/#using-pre-built-images).

## Reporting a vulnerability

Please **do not** open a public GitHub issue for a security vulnerability. Instead, use GitHub's
private reporting:

**[Report a vulnerability](https://github.com/Peppe37/tap/security/advisories/new)**
(Security tab -> "Report a vulnerability")

This opens a private discussion visible only to you and the maintainer, and can turn into a CVE
advisory once fixed. Include:

- What's affected (endpoint, provider adapter, frontend component, etc.)
- Steps to reproduce, or a proof of concept
- What you'd expect to happen instead

Since this is a single-maintainer project, expect an initial response within a few days, not
hours.

## Handling of credentials

Provider credentials (e.g. a 17TRACK API key) are encrypted at rest with a Fernet key
(`app/core/encryption.py`, `TAP_CREDENTIAL_ENCRYPTION_KEY`) -- never logged or printed in plain
text anywhere in the codebase. If you find a code path where a decrypted credential could leak
(logs, error messages, API responses), that's exactly the kind of thing to report privately above.

## What's already automated

Every push and pull request runs, on top of linting and tests:

- `pip-audit` and `bandit` (backend dependency/static analysis) and `pnpm audit` (frontend
  dependencies) -- `.github/workflows/security.yml`
- CodeQL static analysis for Python and JavaScript/TypeScript -- `.github/workflows/codeql.yml`
- `gitleaks`, scanning full git history for committed secrets -- also in `security.yml`
- Dependabot, weekly, for pip/npm/Docker base images/GitHub Actions -- `.github/dependabot.yml`
- SBOM and provenance attestations on every published Docker image --
  `.github/workflows/docker-publish.yml`
