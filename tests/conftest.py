import os
import pytest

TEST_DATABASE_URL_VAR = "FEATURE_GATE_TEST_DATABASE_URL"

@pytest.fixture
def postgres_url():
  """A PostgreSQL URL with the feature_gate tables dropped; skips when unset."""
  url = os.environ.get(TEST_DATABASE_URL_VAR)
  if not url:
    pytest.skip(f"set {TEST_DATABASE_URL_VAR} to run PostgreSQL tests")
  import psycopg
  with psycopg.connect(url, autocommit=True) as connection:
    connection.execute("DROP TABLE IF EXISTS feature_gate_features, feature_gate_schema_migrations")
  return url

@pytest.fixture
def migrated_postgres_url(postgres_url):
  from feature_gate.migrate import main
  main(["--database-url", postgres_url])
  return postgres_url
