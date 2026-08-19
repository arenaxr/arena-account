# Agent Guide

Orientation for agents (and humans) working in this repo. Detailed docs live in the files below — this file is just the index.

## Start here
- [README.md](README.md) — what arena-account is: Django user account management and authentication for the ARENA.
- [REQUIREMENTS.md](REQUIREMENTS.md) — machine- and human-readable reference for features, architecture, and source layout.

## Conventions & development rules
- [CONTRIBUTING.md](CONTRIBUTING.md) — mandatory rules for all contributors, **including agents**: dependency pinning, development rules.

## Tests
- `HOSTNAME=localhost python3 manage.py test` — the full suite (146 tests, SQLite only; no MongoDB or Docker stack needed). `HOSTNAME` is mandatory, and a swallowed 30s MongoDB timeout at startup is expected.
- [users/tests/](users/tests/) — one module per area: MQTT tokens, topics, models, middleware, template tags, utils, health.
- [CONTRIBUTING.md](CONTRIBUTING.md) — setup, and how to run a single module or single test.

## MQTT authentication
- [docs/mqtt-v1.md](docs/mqtt-v1.md) — sample MQTT JWT topic permissions v1 (deprecated).
- [docs/mqtt-v2.md](docs/mqtt-v2.md) — sample MQTT JWT topic permissions v2.

## Release history
- [CHANGELOG.md](CHANGELOG.md) — generated release history (release-please; Conventional Commits).
