# Contributing to ARENA Account

The general Contribution Guide for all ARENA projects can be found [here](https://docs.arenaxr.org/content/contributing.html).

This document covers **development rules and conventions** specific to this repository. These rules are mandatory for all contributors, including automated/agentic coding tools.

## Development Rules

### 1. Dependencies — Pin All Versions

**All dependencies must use exact, pegged versions** (no `^`, `~`, or `*` ranges). This prevents version drift across environments and ensures reproducible builds for security.

## Local Development

To develop the `arena-account` locally:
1. Run `init-config.sh` in the parent `arena-services-docker` directory to generate the required `.env` secrets and configuration files.
2. Start the local stack using `docker-compose -f docker-compose.localdev.yaml up -d arena-account`
3. The Django source folder is mounted via the localdev compose file. For testing or migrations, you can exec into the container and use `manage.py`.

That container route is what you want for migrations against the live stack. For the unit test suite you do not need the stack at all — see [Testing](#testing) below for the standalone route.

## Testing

The Django test suite runs standalone — it uses a throwaway SQLite database and needs neither the `arena-services-docker` stack nor MongoDB. Run it before committing; CI runs the same command on every PR and push to `main`.

```sh
python3.12 -m venv env && . env/bin/activate   # Django 6.0 needs 3.12 or newer; CI runs 3.14
pip install -r requirements.txt
HOSTNAME=localhost python3 manage.py test
```

`HOSTNAME` is mandatory: `users/startup.py` stores it as the `django_site` name, and without it the test database migration fails with `IntegrityError: NOT NULL constraint failed: django_site.name`. Putting `HOSTNAME=localhost` in your local `.env` also works, since `manage.py` calls `load_dotenv()` — but `make test` sets neither, so use one or the other.

The 146 tests take about 10s, yet the run takes about 40s. `post_migrate` calls `get_persist_db()`, which waits out a 30s MongoDB server-selection timeout and prints:

```
arena_persist: connecting...
arena_persist: error: mongodb:27017: [Errno -2] Name or service not known ... Timeout: 30s
```

The exact error text varies with your resolver: a host that cannot resolve `mongodb` reports `Name or service not known`, one that resolves it reports a refused connection. Either way, outside the Docker stack this is expected — `users/persist_db.py` catches it and the suite still reports `OK`. `Error: keyfile not found` and `Service Unavailable: /user/health` in the output are expected too.

To narrow while iterating:

```sh
HOSTNAME=localhost python3 manage.py test users.tests.test_mqtt_match
HOSTNAME=localhost python3 manage.py test users.tests.test_utils.ParsePersistDateTests.test_iso_string_with_zulu_suffix
```

Only two of the eight modules are database-backed: `test_health` and `test_mqtt_token`, the only two that use Django's `TestCase`. Every other module — `test_middleware`, `test_models`, `test_mqtt_match`, `test_mqtt_topics`, `test_templatetags`, `test_utils` — uses `SimpleTestCase` or plain `unittest.TestCase`, so the runner skips test-database creation altogether: each finishes in under a second and never waits on MongoDB. `test_health` takes about 30s and `test_mqtt_token` about 40s, almost all of it that wait.

## Code Style
- Follow standard Python formatting guidelines (`black` and `PEP 8`).
- Ensure all HTTP handlers return standard JSON payloads.

The `arena-account` uses [Release Please](https://github.com/googleapis/release-please) to automate CHANGELOG generation and semantic versioning. Your PR titles *must* follow Conventional Commit standards (e.g., `feat:`, `fix:`, `chore:`).

> [!CAUTION]
> **Never use `BREAKING CHANGE` in commit/PR bodies or the `!` suffix on commit/PR types (e.g., `feat!:`, `fix!:`).** These tokens cause release-please to automatically bump the major version. Major version increments are reserved for the maintainer's explicit decision — contributors and agents do not decide what constitutes a breaking change for semver purposes.


## CI & Dependency Management Conventions
- **GitHub Actions Tag SHA Pinning**: All GitHub Action references in `.github/workflows/` MUST be pinned to the exact commit SHA of the official release tag (e.g., `uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0`).
- **Inline Version Comments**: The inline comment next to the SHA MUST specify the exact tag version used. This enables Dependabot to recognize the release version, generate human-readable SemVer PR titles (`from X.Y.Z to A.B.C`), and automatically update version comments during upgrades.