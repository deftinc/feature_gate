# FeatureGate

Featuregate is a simple feature flag API similar to [Flipper](https://github.com/flippercloud/flipper).

## Configuration

### PosthogAdapter

```bash
export POSTHOG_API_KEY="someapikey"
export POSTHOG_PROJECT_ID="someprojectid"
export POSTHOG_API_BASE="https://us.posthog.com" # Optional, defaults to US Cloud
```

`POSTHOG_API_KEY` must be a personal API key with the `feature_flag:read` and `feature_flag:write` scopes. EU Cloud users should set `POSTHOG_API_BASE="https://eu.posthog.com"`; self-hosted users should use their own domain.

### PostgresAdapter

Install the optional PostgreSQL dependency (psycopg 3):

```bash
pip install "feature_gate[postgres]"
```

Point it at your database:

```bash
export FEATURE_GATE_DATABASE_URL="postgresql://user:pass@localhost:5432/myapp" # Falls back to DATABASE_URL
export FEATURE_GATE_TABLE_PREFIX="feature_gate_"                               # Optional, this is the default
```

Every table and function feature_gate creates starts with the table prefix, which defaults to `feature_gate_`. Change it if those names clash with something in your database. The prefix may only contain lowercase letters, digits and underscores, can't start with a digit, and can be at most 46 characters. The migrations and the adapter must use the same prefix.

Create the tables by running the migrations against that database. Do this once when you set it up, and again after you upgrade `feature_gate`:

```bash
feature-gate-migrate                                  # uses FEATURE_GATE_DATABASE_URL, then DATABASE_URL
feature-gate-migrate --database-url postgresql://...  # or pass it explicitly
feature-gate-migrate --table-prefix flags_            # uses FEATURE_GATE_TABLE_PREFIX, then feature_gate_
```

The migrations create the tables and function described under [Schema](#schema). Running the command again only applies new migrations. Each prefix has its own migration history, so two prefixes can live side by side in one database. A PostgreSQL advisory lock stops two deploys from migrating at the same time. To run migrations from Python, for example inside your own migration tool, use `feature_gate.migrate.migrate(connection, table_prefix="feature_gate_")` with an autocommit psycopg connection.

#### Schema

The names below use the default `feature_gate_` prefix; with a custom prefix, swap it in, e.g. `flags_features`.

`feature_gate_features` has one row for each feature:

| Column        | Type          | Notes                                                                 |
|---------------|---------------|-----------------------------------------------------------------------|
| `id`          | `uuid`        | Primary key, a UUIDv7 that defaults to `feature_gate_uuidv7()`. UUIDv7s sort by creation time, so `features()` orders by `id` to return features in the order they were added. |
| `key`         | `text`        | `NOT NULL`, `UNIQUE`. The key you pass to `is_enabled`, `enable`, `disable` and `remove`. |
| `name`        | `text`        | `Feature.name`.                                                        |
| `description` | `text`        | `Feature.description`.                                                 |
| `enabled`     | `boolean`     | `NOT NULL`, defaults to `false`. A new feature starts out disabled.    |
| `created_at`  | `timestamptz` | `NOT NULL`, defaults to `now()`.                                       |
| `updated_at`  | `timestamptz` | `NOT NULL`, defaults to `now()`. Updated by `enable` and `disable`.    |

`feature_gate_schema_migrations` has one row for each migration that has been applied:

| Column       | Type          | Notes                                                        |
|--------------|---------------|--------------------------------------------------------------|
| `version`    | `text`        | Primary key. The migration's file name without `.sql`, e.g. `0001_create_features`. |
| `applied_at` | `timestamptz` | `NOT NULL`, defaults to `now()`.                             |

The migrations also create the function `feature_gate_uuidv7()`. PostgreSQL 18 has a built-in `uuidv7()`, but this function works on PostgreSQL 13 and later. Like the built-in, it fills the 12 bits after the millisecond timestamp with sub-millisecond clock precision, so IDs created one after another sort in that order.

`remove` deletes the feature's row; nothing is soft-deleted. Change these tables only by adding migrations, never by hand, because `feature-gate-migrate` assumes they match what its migrations created.

```python
from feature_gate.adapters import PostgresAdapter

adapter = PostgresAdapter()                                 # reads the env vars above
adapter = PostgresAdapter(database_url="postgresql://...")  # or pass a URL
adapter = PostgresAdapter(connection=existing_psycopg_conn) # or reuse a psycopg 3 connection
adapter = PostgresAdapter(table_prefix="flags_")            # match the prefix you migrated with
```

When you pass in a connection that is already inside a transaction, the adapter's writes become part of that transaction and are committed only when you commit.

### Logging

FeatureGate logs through [structlog](https://www.structlog.org/). Every adapter takes an optional `logger=`; without one it uses `structlog.get_logger()`, so its logs follow your application's structlog configuration (structlog's default is colored console output on stdout). Log events carry their data as fields (`feature`, `response`, `klass`, and so on), so any structlog renderer can output them.

To get structured JSON logs, pick one of the following.

**JSON from FeatureGate only.** Pass a `json_logger`, which writes one JSON object per line to stdout or to any file you give it, regardless of your structlog configuration:

```python
import sys
from feature_gate.adapters import PostgresAdapter
from feature_gate.structured_logging import json_logger

adapter = PostgresAdapter(logger=json_logger())                       # stdout
adapter = PostgresAdapter(logger=json_logger(sys.stderr))             # stderr
adapter = PostgresAdapter(logger=json_logger(open("logs/feature_gate.log", "a")))  # a file
```

**JSON from your whole application.** Configure structlog globally with FeatureGate's processor chain (or your own ending in `structlog.processors.JSONRenderer()`); adapters created without a `logger=` will pick it up:

```python
import structlog
from feature_gate.structured_logging import PROCESSORS

structlog.configure(processors=PROCESSORS)
```

**Your own logger.** Any structlog-style logger with `info` and `error` methods works, e.g. `MemoryAdapter(logger=structlog.get_logger("feature_gate"))`.

Each line from `json_logger` or `PROCESSORS` looks like:

```json
{"feature": "test_flag", "response": true, "event": "enable feature", "klass": "PostgresAdapter", "level": "info", "timestamp": "2026-10-26T23:03:18.778271Z"}
```

## Usage

```python
from feature_gate.client import Client
from feature_gate.adapters import PosthogAdapter
from feature_gate.feature import Feature

adapter = PosthogAdapter() # Or MemoryAdapter for testing
client = Client(adapter)
feature = Feature("Test flag", "test_flag", "This is a test flag")

client.features()
# => []

client.add(feature)
# => True

client.features()
# => ["test_flag"]

client.is_enabled("test_flag")
# => False

client.enable("test_flag")
# => True

client.is_enabled("test_flag")
# => True

client.disable("test_flag")
# => True

client.is_enabled("test_flag")
# => False

client.remove("test_flag")
# => True

client.features()
# => []
```

## Errors

### FeatureNotFound
If you try to run something that presumes the existence of a feature and it can't find it it'll throw a `FeatureNotFound`.

```python
from feature_gate.client import FeatureNotFound

try:
  client.remove("some_feature_that_definitely_does_not_exist")
except FeatureNotFound as err:
  # Do what we want to do when the feature doesn't exist
```

### PosthogApiClientError
For the `PosthogAdapter` in particular it will raise error if it was unable to reach the Posthog API. These get bubbled up as `PosthogAPIClientError`.

```python
from feature_gate.clients.posthog_api_client import PosthogAPIClientError

try:
  client.features() #disable network connection
except PosthogAPIClientError as err:
  # Handle the error -- define default behavior in outage
```

### RateLimitError
Again, specific to the `PosthogAdapter` it will raise an error if the account is rate limited by the Posthog API. These get bubbled up as `RateLimitError`.

```python
from feature_gate.clients.posthog_api_client import RateLimitError

try:
  client.features() # receives response indicating a rate limit and retry time in seconds
except RateLimitError as err:
  # Handle the error -- define default behavior during rate limiting
```

## Testing

The Memory Adapter can be used for writing tests. This creates an ephemeral memory only implementation of the feature_gate client API. This is non-suitable for production only for tests.

```python
from feature_gate.client import Client
from feature_gate.adapters.memory import MemoryAdapter

client = Client(MemoryAdapter())
```

## Developing this library

Tool versions (Python and [uv](https://docs.astral.sh/uv/)) are pinned in `.tool-versions` and installed with [asdf](https://asdf-vm.com/).

```bash
bin/bootstrap # first-time setup
bin/ci        # install dependencies and run the tests
```

The PostgreSQL tests are skipped unless `FEATURE_GATE_TEST_DATABASE_URL` points at a database they're allowed to modify. They drop and recreate the tables and functions for the `feature_gate_` and `custom_ff_` prefixes.

```bash
createdb feature_gate_test
FEATURE_GATE_TEST_DATABASE_URL=postgresql://localhost/feature_gate_test uv run pytest -vv
```

### Hot-reload the REPL

Hot-reload the client in the repl for development:

```
$ bin/repl
>>> exec(open('reload.py').read())
```
