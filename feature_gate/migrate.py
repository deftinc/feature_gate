import argparse
import os
import re
import sys
from importlib import resources

# Arbitrary constant so concurrent migrators (e.g. parallel deploys) serialize.
ADVISORY_LOCK_KEY = 7_465_617_475_726_516
DEFAULT_TABLE_PREFIX = "feature_gate_"
# PostgreSQL truncates identifiers at 63 bytes; leave room for the longest
# suffix, "schema_migrations".
MAX_TABLE_PREFIX_LENGTH = 63 - len("schema_migrations")
TABLE_PREFIX_PATTERN = re.compile(r"[a-z_][a-z0-9_]*")

class MigrationError(RuntimeError):
  pass

def database_url_from_env():
  return os.environ.get("FEATURE_GATE_DATABASE_URL") or os.environ.get("DATABASE_URL")

def table_prefix_from_env():
  return os.environ.get("FEATURE_GATE_TABLE_PREFIX") or DEFAULT_TABLE_PREFIX

def validate_table_prefix(table_prefix):
  """Return the prefix if it is safe to interpolate into SQL, else raise ValueError."""
  if not TABLE_PREFIX_PATTERN.fullmatch(table_prefix or ""):
    raise ValueError(f"table prefix {table_prefix!r} must be lowercase letters, digits, and underscores, not starting with a digit")
  if len(table_prefix) > MAX_TABLE_PREFIX_LENGTH:
    raise ValueError(f"table prefix {table_prefix!r} is longer than {MAX_TABLE_PREFIX_LENGTH} characters")
  return table_prefix

def available_migrations(table_prefix=DEFAULT_TABLE_PREFIX):
  validate_table_prefix(table_prefix)
  files = resources.files("feature_gate.migrations")
  return sorted(
    (entry.name.removesuffix(".sql"), entry.read_text().replace("{prefix}", table_prefix))
    for entry in files.iterdir()
    if entry.name.endswith(".sql")
  )

def applied_migrations(connection, table_prefix=DEFAULT_TABLE_PREFIX):
  rows = connection.execute(f"SELECT version FROM {table_prefix}schema_migrations").fetchall()
  return {row[0] for row in rows}

def migrate(connection, table_prefix=DEFAULT_TABLE_PREFIX):
  """Apply pending migrations; returns the versions applied by this run.

  Expects an autocommit connection: each migration runs in its own transaction.
  Each table prefix has its own tables and migration history.
  """
  validate_table_prefix(table_prefix)
  if not connection.autocommit:
    raise MigrationError("migrate requires an autocommit connection")
  schema_migrations_table = f"{table_prefix}schema_migrations"
  applied = []
  connection.execute("SELECT pg_advisory_lock(%s)", (ADVISORY_LOCK_KEY,))
  try:
    connection.execute(f"""
      CREATE TABLE IF NOT EXISTS {schema_migrations_table} (
        version text PRIMARY KEY,
        applied_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    already_applied = applied_migrations(connection, table_prefix)
    for version, sql in available_migrations(table_prefix):
      if version in already_applied:
        continue
      with connection.transaction():
        connection.execute(sql)
        connection.execute(
          f"INSERT INTO {schema_migrations_table} (version) VALUES (%s)",
          (version,),
        )
      applied.append(version)
  finally:
    connection.execute("SELECT pg_advisory_unlock(%s)", (ADVISORY_LOCK_KEY,))
  return applied

def main(argv=None):
  parser = argparse.ArgumentParser(
    prog="feature-gate-migrate",
    description="Create or update the feature_gate tables in a PostgreSQL database.",
  )
  parser.add_argument(
    "--database-url",
    default=None,
    help="PostgreSQL connection URL (default: $FEATURE_GATE_DATABASE_URL, then $DATABASE_URL)",
  )
  parser.add_argument(
    "--table-prefix",
    default=None,
    help=f"prefix for the tables and function feature_gate creates (default: $FEATURE_GATE_TABLE_PREFIX, then {DEFAULT_TABLE_PREFIX})",
  )
  args = parser.parse_args(argv)
  database_url = args.database_url or database_url_from_env()
  if not database_url:
    parser.error("no database URL: pass --database-url or set FEATURE_GATE_DATABASE_URL or DATABASE_URL")
  table_prefix = args.table_prefix or table_prefix_from_env()
  try:
    validate_table_prefix(table_prefix)
  except ValueError as error:
    parser.error(str(error))

  import psycopg

  with psycopg.connect(database_url, autocommit=True) as connection:
    applied = migrate(connection, table_prefix)
  if applied:
    for version in applied:
      print(f"Applied {version}")
  else:
    print("No pending migrations.")
  return 0

if __name__ == "__main__":
  sys.exit(main())
