# tap — Track All Packs

An open source, self-hosted platform for tracking packages across multiple carriers and
marketplaces — InPost, Poste Italiane, BRT, GLS, and any carrier covered by a third-party
aggregator — from one dashboard, on your own infrastructure.

## Why

Every carrier has its own tracking page, its own quirks, and its own coverage gaps. tap gives you
one place to add a tracking number, tell it where you bought the item and who is shipping it, and
let it pick the best available way to follow the shipment: an official carrier API where one
exists, a maintained scraper where it doesn't, or a third-party aggregator as a fallback.

## Features

- **Multi-user** — designed for a household, a team, or any group of self-hosters sharing one
  instance, with per-user data isolation and an admin role.
- **Pluggable tracking providers** — a carrier can be tracked through more than one method
  (official API, scraper, aggregator); you choose which one to use per package. See
  [Adding a provider](ADDING_A_PROVIDER.md) to add support for a new carrier.
- **Guided onboarding** — first boot walks you through creating the admin account; providers that
  need a personal API key (e.g. an aggregator) come with step-by-step setup instructions and a
  "test connection" check before you save anything.
- **Automatic polling** — a Celery worker refreshes active packages on a schedule that speeds up
  while a package is out for delivery and stops once it's delivered, with per-provider rate
  limiting and exponential backoff on failures.
- **On-demand refresh** — don't want to wait for the next scheduled check? Refresh any package
  from its detail page.

## Where to go next

- **[Self-hosting](self-hosting.md)** — run tap with Docker Compose, environment variables,
  backup notes.
- **[Architecture](ARCHITECTURE.md)** — data model, provider plugin system, async polling design.
- **[Adding a provider](ADDING_A_PROVIDER.md)** — implement a new carrier API, scraper, or
  aggregator integration.
- **[Contributing](contributing.md)** — local dev setup, checks to run before a pull request,
  commit message conventions.

## License

MIT — see [LICENSE](https://github.com/Peppe37/tap/blob/main/LICENSE).
