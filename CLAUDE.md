# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`feature_gate` is a small Python feature-flag library (published to PyPI) modeled on Ruby's Flipper. Dependencies are managed with uv (`pyproject.toml` + `uv.lock`, built with hatchling); Python and uv versions are pinned in `.tool-versions` (asdf). Supports Python >= 3.10.

## Commands

```bash
bin/bootstrap                 # first-time setup (brew, asdf, then bin/update)
bin/update                    # asdf plugins/tools + `uv sync --locked`
bin/ci                        # bin/update, then `uv run pytest -vv`
uv run pytest -vv             # run all tests
uv run --isolated --python 3.10 pytest -vv  # run against the oldest supported Python
FEATURE_GATE_TEST_DATABASE_URL=postgresql://localhost/feature_gate_test uv run pytest -vv  # include PostgreSQL tests
uv run pytest tests/feature_gate/adapters/posthog_test.py::test_add_returns_true_when_feature_does_exist  # single test
bin/repl                      # interactive REPL with repl.py loaded (posthog_client() helper)
```

Run pytest from the repo root: fixtures are loaded with relative paths (`./tests/fixtures/...`). Test files use the `*_test.py` naming convention.

## Architecture

Three layers, each delegating to the next:

1. **`Client`** (`feature_gate/client.py`) — public API (`add`, `remove`, `features`, `is_enabled`, `enable`, `disable`). It forwards every call to its adapter and logs via `adapter.logger`. `FeatureNotFound` lives here and is imported by the other layers.
2. **Adapters** (`feature_gate/adapters/`) — duck-typed backends implementing the same six methods plus a `logger` attribute. There is no base class; `tests/fixtures/null_adapter.py` is the de facto interface reference.
   - `MemoryAdapter` — in-process list of dicts; intended for tests only.
   - `PostgresAdapter` — psycopg 3 (optional extra `feature_gate[postgres]`, imported lazily so the other adapters work without it). Stores flags in a single `<prefix>features` table (`key` unique, `enabled` boolean; `id` is a UUIDv7 from the migration-defined `<prefix>uuidv7()`, which supports PostgreSQL < 18, and `features()` is ordered by `id`). The table prefix defaults to `feature_gate_`, is set by `table_prefix=` / `--table-prefix` / `FEATURE_GATE_TABLE_PREFIX`, and is checked by `validate_table_prefix` before it's interpolated into SQL. Each call runs in `connection.transaction()`, so a caller-supplied connection that's mid-transaction gets a savepoint, not a commit. Raises `FeatureNotFound` like `MemoryAdapter`.
   - `PosthogAdapter` — wraps `PosthogAPIClient` and translates its `{"data": ...}` envelopes into plain return values.
3. **`PosthogAPIClient`** (`feature_gate/clients/posthog_api_client.py`) — raw HTTP to the PostHog feature-flags API via `requests`. Responses are normalized to `{"data": ..., "pagination": ...}` on success or `{"errors": [...]}` on non-429 failures. HTTP 429 raises `RateLimitError`; `requests.ConnectionError` is converted to `PosthogAPIClientError`. Features are looked up by key by listing all flags (`fetch_feature`), then patched by PostHog `id`; removal is a soft delete (`PATCH deleted: true`).

PostgreSQL schema changes are numbered SQL files in `feature_gate/migrations/` (shipped in the wheel, loaded with `importlib.resources`), applied by `feature_gate/migrate.py`, which is exposed as the `feature-gate-migrate` console script. Add a new `NNNN_*.sql` file for each schema change and never edit one that has shipped. Write every object name as `{prefix}name`; `available_migrations` substitutes the configured prefix. Applied versions are tracked per prefix in `<prefix>schema_migrations`.

`Feature` (`feature_gate/feature.py`) is a plain value object (`name`, `key`, `description`). Adapters' `add` takes a `Feature`; all other methods take the feature key string. Note that `PosthogAPIClient.create_feature` sends the feature *description* as PostHog's `name` field.

Large blocks of commented-out methods in `Client` and `PosthogAdapter` are a Flipper-parity roadmap (actors, groups, percentages, expressions), not dead code to remove.

### Configuration and logging

- `PosthogAPIClient` falls back to env vars `POSTHOG_API_KEY`, `POSTHOG_PROJECT_ID`, and `POSTHOG_API_BASE` (default `https://us.posthog.com`; EU Cloud is `https://eu.posthog.com`) when constructor args are `None`.
- Adapters/clients call `structlog.configure(...)` globally in `__init__` and write JSON logs to files: `PosthogAPIClient` → `$PROJECT_ROOT/logs/development.log` (append), `MemoryAdapter` → `./logs/feature_gate.log` (truncate). Context is bound with `structlog.contextvars`.

## Testing conventions

- PostHog tests never hit the network: they `patch.object(requests, 'get'|'post'|'patch', return_value=...)` using the `Mock` response builders in `tests/fixtures/posthog_api_client/mocks.py`, which load JSON from `tests/fixtures/posthog_api_client/*.json`. Add a new JSON fixture + `mock_*` builder for new response shapes.
- PostgreSQL tests (`postgres_test.py`, `migrate_test.py`) use the `postgres_url` / `migrated_postgres_url` fixtures in `tests/conftest.py`, which skip unless `FEATURE_GATE_TEST_DATABASE_URL` is set and drop the tables and functions for each prefix in `TEST_TABLE_PREFIXES` (`feature_gate_`, `custom_ff_`) before each test. `.github/workflows/ci.yml` runs the suite on every pull request across Python 3.10/3.15 × PostgreSQL 16/18 service containers; the release workflow also runs them against `postgres:16` before publishing.
- `Client` tests use `NullAdapter` to isolate the client from any backend.

## Code style

Two-space indentation throughout (not PEP 8's four). Classes expose attributes alongside same-named accessor methods (e.g. `self.logger` and `def logger`); the instance attribute shadows the method, so access them as attributes.

## Releasing

Bump the version in both `VERSION` and `pyproject.toml` (they must match), merge to `main`, then run `bin/publish`, which tags `vX.Y.Z` and pushes the tag. The tag push triggers `.github/workflows/python-publish.yml`, which runs the tests, then `uv build` and `uv publish` to PyPI using the `PYPI_API_TOKEN` secret.
