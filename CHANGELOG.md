## [0.3.0](https://github.com/Peppe37/tap/compare/v0.2.0...v0.3.0) (2026-08-13)

### Features

* add Postgres backup/restore scripts, verified against docker compose ([7de65c3](https://github.com/Peppe37/tap/commit/7de65c323d01e3527fde01c6b111801db68f7bd3))
* **backend:** add a database/redis readiness check ([f02ff13](https://github.com/Peppe37/tap/commit/f02ff1336bc69b7ba68d2f9e414525a0014bb5e0))
* **backend:** add API-wide rate limiting ([15469bd](https://github.com/Peppe37/tap/commit/15469bd6a68f0806fe04aae4bfb9caf1738d020e))

### Bug Fixes

* **providers:** enforce 17TRACK's real 3 req/s limit, not just 30/min ([f4f7d83](https://github.com/Peppe37/tap/commit/f4f7d8381a987c04bb471f95cd820f9664a57542))

## [0.2.0](https://github.com/Peppe37/tap/compare/v0.1.1...v0.2.0) (2026-08-02)

### Features

* add an Uptime Kuma-style update-available notification ([a0f3603](https://github.com/Peppe37/tap/commit/a0f3603c814f939be36cf0968e86bb7c31bf3899))

## [0.1.1](https://github.com/Peppe37/tap/compare/v0.1.0...v0.1.1) (2026-08-02)

### Bug Fixes

* **providers:** fall back to InPost's Italian ShipX instance ([a2baf1f](https://github.com/Peppe37/tap/commit/a2baf1f569b83055405fb9ef94432ca099b99c94))
