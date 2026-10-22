import argparse
import os
import sys
from importlib import resources

# Arbitrary constant so concurrent migrators (e.g. parallel deploys) serialize.
ADVISORY_LOCK_KEY = 7_465_617_475_726_516
SCHEMA_MIGRATIONS_TABLE = "feature_gate_schema_migrations"

class MigrationError(RuntimeError):
  pass

def database_url_from_env():
  return os.environ.get("FEATURE_GATE_DATABASE_URL") or os.environ.get("DATABASE_URL")

def available_migrations():
  files = resources.files("feature_gate.migrations")
  return sorted(
    (entry.name.removesuffix(".sql"), entry.read_text())
    for entry in files.iterdir()
    if entry.name.endswith(".sql")
  )

def applied_migrations(connection):
  rows = connection.execute(f"SELECT version FROM {SCHEMA_MIGRATIONS_TABLE}").fetchall()
  return {row[0] for row in rows}

def migrate(connection):
  """Apply pending migrations; returns the versions applied by this run.

  Expects an autocommit connection: each migration runs in its own transaction.
  """
  if not connection.autocommit:
    raise MigrationError("migrate requires an autocommit connection")
  applied = []
  connection.execute("SELECT pg_advisory_lock(%s)", (ADVISORY_LOCK_KEY,))
  try:
    connection.execute(f"""
      CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
        version text PRIMARY KEY,
        applied_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    already_applied = applied_migrations(connection)
    for version, sql in available_migrations():
      if version in already_applied:
        continue
      with connection.transaction():
        connection.execute(sql)
        connection.execute(
          f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (version) VALUES (%s)",
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
  args = parser.parse_args(argv)
  database_url = args.database_url or database_url_from_env()
  if not database_url:
    parser.error("no database URL: pass --database-url or set FEATURE_GATE_DATABASE_URL or DATABASE_URL")

  import psycopg

  with psycopg.connect(database_url, autocommit=True) as connection:
    applied = migrate(connection)
  if applied:
    for version in applied:
      print(f"Applied {version}")
  else:
    print("No pending migrations.")
  return 0

if __name__ == "__main__":
  sys.exit(main())
