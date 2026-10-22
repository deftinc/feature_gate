import os
import pytest

TEST_DATABASE_URL_VAR = "FEATURE_GATE_TEST_DATABASE_URL"
# Prefixes the PostgreSQL tests create objects under; dropped before each test.
TEST_TABLE_PREFIXES = ["feature_gate_", "custom_ff_"]

@pytest.fixture
def postgres_url():
  """A PostgreSQL URL with the test prefixes' tables and functions dropped; skips when unset."""
  url = os.environ.get(TEST_DATABASE_URL_VAR)
  if not url:
    pytest.skip(f"set {TEST_DATABASE_URL_VAR} to run PostgreSQL tests")
  import psycopg
  with psycopg.connect(url, autocommit=True) as connection:
    for prefix in TEST_TABLE_PREFIXES:
      connection.execute(f"DROP TABLE IF EXISTS {prefix}features, {prefix}schema_migrations")
      connection.execute(f"DROP FUNCTION IF EXISTS {prefix}uuidv7()")
  return url

@pytest.fixture
def migrated_postgres_url(postgres_url):
  from feature_gate.migrate import main
  main(["--database-url", postgres_url])
  return postgres_url
