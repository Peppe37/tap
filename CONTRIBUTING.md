# Contributing

Thanks for considering contributing to tap. This is a self-hosted project maintained by and for
its users — issues, bug reports, and pull requests are all welcome.

## Getting set up

See the "Local development" section of the
[README](https://github.com/Peppe37/tap#local-development) for backend and frontend setup.
You'll need PostgreSQL and Redis running locally (or use `docker compose up postgres redis` from
the repo root to run just those two).

## Before opening a pull request

Backend (`cd backend`):

```bash
ruff check .
ruff format --check .
mypy app
pytest --cov=app
```

Frontend (`cd frontend`):

```bash
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm build
```

All of the above run in CI (`.github/workflows/ci.yml`) on every pull request; running them
locally first saves a round-trip.

If `pre-commit` is installed (`pip install pre-commit`), run `pre-commit install` once to get
the fast checks (formatting, linting) automatically on every commit, and
`pre-commit install --hook-type commit-msg` once to also validate commit message format (see
below) before it's written.

## Adding a carrier or tracking method

See [Adding a provider](https://github.com/Peppe37/tap/blob/main/docs/ADDING_A_PROVIDER.md) —
this is almost certainly the most common kind of contribution, and has a dedicated walkthrough.

## Commit messages and pull requests

- Keep pull requests focused; unrelated cleanup makes review harder.
- Write commit messages and PR descriptions around *why*, not just *what* — the diff already
  shows what changed.
- Add or update tests for behavior you add or change. A bug fix without a regression test is easy
  to reintroduce.

### Conventional Commits

Every commit message must follow [Conventional Commits](https://www.conventionalcommits.org/):
`<type>(<scope>): <description>`, e.g. `fix(providers): handle 17TRACK rate-limit responses`.
`type` is one of `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`,
`chore`, `revert`. This isn't just style — merges to `main` are released automatically by
[semantic-release](https://semantic-release.gitbook.io/) based on these prefixes: a `fix` cuts a
patch release, a `feat` a minor release, and a `BREAKING CHANGE:` footer (or `!` after the type)
a major release. Anything else (`docs`, `chore`, `ci`, ...) doesn't trigger a release at all.
`pre-commit install --hook-type commit-msg` (see above) checks this locally; CI checks it again
on every pull request.

Releases themselves (version, `CHANGELOG.md`, GitHub Release) are entirely automated by
`.github/workflows/release.yml` on every push to `main` — there's nothing to do manually, and
backend/frontend `package.json`/`pyproject.toml` versions are intentionally not kept in lockstep
with release tags; the tag and `CHANGELOG.md` are the source of truth for "what version is this".

## Reporting issues

Open a GitHub issue with: what you expected, what happened instead, and — for a tracking
provider issue — which carrier/provider/tracking number pattern is affected (not the tracking
number itself if it identifies a real shipment; a redacted or synthetic example is fine).
