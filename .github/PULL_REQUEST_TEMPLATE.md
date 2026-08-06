## What and why

<!-- What does this change, and why -- the diff already shows what, focus on the why. -->

## Checklist

- [ ] Commit messages follow [Conventional Commits](https://Peppe37.github.io/tap/contributing/#conventional-commits)
- [ ] Backend: `ruff check .`, `ruff format --check .`, `mypy app`, `pytest --cov=app` all pass
- [ ] Frontend: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`, `pnpm build` all pass
- [ ] Added/updated tests for any behavior change
- [ ] If this touches a `TrackingProvider` implementation: the endpoint/response shape/status
      values are verified against the real carrier (docs, direct request, or existing verified
      code) -- not guessed. See [docs/ADDING_A_PROVIDER.md](https://Peppe37.github.io/tap/ADDING_A_PROVIDER/).
- [ ] Updated documentation (`README.md`, `docs/`) if this changes user-facing behavior
