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

## Code Style
- Follow standard Python formatting guidelines (`black` and `PEP 8`).
- Ensure all HTTP handlers return standard JSON payloads.

The `arena-account` uses [Release Please](https://github.com/googleapis/release-please) to automate CHANGELOG generation and semantic versioning. Your PR titles *must* follow Conventional Commit standards (e.g., `feat:`, `fix:`, `chore:`).


## CI & Dependency Management Conventions
- **GitHub Actions Tag SHA Pinning**: All GitHub Action references in `.github/workflows/` MUST be pinned to the exact commit SHA of the official release tag (e.g., `uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0`).
- **Inline Version Comments**: The inline comment next to the SHA MUST specify the exact tag version used. This enables Dependabot to recognize the release version, generate human-readable SemVer PR titles (`from X.Y.Z to A.B.C`), and automatically update version comments during upgrades.