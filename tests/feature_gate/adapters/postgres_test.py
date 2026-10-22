import uuid
import psycopg
import pytest
from feature_gate.client import Client, FeatureNotFound
from feature_gate.adapters.postgres import PostgresAdapter
from feature_gate.feature import Feature

@pytest.fixture
def client(migrated_postgres_url):
  adapter = PostgresAdapter(database_url=migrated_postgres_url)
  yield Client(adapter)
  adapter.connection.close()

def build_feature(key="test_feature"):
  return Feature(key, key, "This is a test feature")

def test_client_initialization(client):
  assert isinstance(client.adapter, PostgresAdapter)

def test_add_feature(client):
  assert client.add(build_feature())
  assert "test_feature" in client.features()

def test_add_feature_persists_name_and_description(client, migrated_postgres_url):
  client.add(Feature("Test feature", "test_feature", "This is a test feature"))
  with psycopg.connect(migrated_postgres_url) as connection:
    row = connection.execute(
      "SELECT name, description, enabled FROM feature_gate_features WHERE key = 'test_feature'"
    ).fetchone()
  assert row == ("Test feature", "This is a test feature", False)

def test_ids_are_uuidv7_in_creation_order(client, migrated_postgres_url):
  keys = [f"feature_{i}" for i in range(50)]
  for key in keys:
    client.add(build_feature(key))
  with psycopg.connect(migrated_postgres_url) as connection:
    rows = connection.execute("SELECT id, created_at FROM feature_gate_features").fetchall()
  ids = [row[0] for row in rows]
  assert all(id.version == 7 and id.variant == uuid.RFC_4122 for id in ids)
  assert len(set(ids)) == len(keys)
  for id, created_at in rows:
    unix_ms = id.int >> 80
    assert abs(unix_ms - created_at.timestamp() * 1000) < 1000
  assert client.features() == keys

def test_features_are_listed_in_insertion_order(client):
  for key in ["zebra", "apple", "mango"]:
    client.add(build_feature(key))
  assert client.features() == ["zebra", "apple", "mango"]

def test_remove_feature(client):
  client.add(build_feature())
  assert client.remove("test_feature")
  assert "test_feature" not in client.features()

def test_enable_feature(client):
  client.add(build_feature())
  assert client.enable("test_feature")

def test_is_enabled_feature(client):
  client.add(build_feature())
  assert not client.is_enabled("test_feature")
  assert client.enable("test_feature")
  assert client.is_enabled("test_feature")
  assert client.disable("test_feature")
  assert not client.is_enabled("test_feature")

def test_enabled_state_is_shared_across_adapters(client, migrated_postgres_url):
  client.add(build_feature())
  client.enable("test_feature")
  other = PostgresAdapter(database_url=migrated_postgres_url)
  assert other.is_enabled("test_feature")
  other.connection.close()

def test_is_enabled_feature_not_found(client):
  with pytest.raises(FeatureNotFound):
    client.is_enabled("test_feature")

def test_enable_feature_not_found(client):
  with pytest.raises(FeatureNotFound):
    client.enable("test_feature")

def test_disable_feature_not_found(client):
  with pytest.raises(FeatureNotFound):
    client.disable("test_feature")

def test_remove_feature_not_found(client):
  with pytest.raises(FeatureNotFound):
    client.remove("test_feature")

def test_add_feature_twice_does_not_duplicate(client):
  assert client.add(build_feature())
  assert client.add(build_feature())
  assert client.features() == ["test_feature"]

def test_feature_not_found_message_includes_key(client):
  with pytest.raises(FeatureNotFound, match="Feature test_feature not found."):
    client.is_enabled("test_feature")

def test_reconnects_when_connection_is_closed(client):
  client.add(build_feature())
  client.adapter.connection.close()
  assert client.features() == ["test_feature"]

def test_accepts_an_existing_connection(migrated_postgres_url):
  with psycopg.connect(migrated_postgres_url, autocommit=True) as connection:
    adapter = PostgresAdapter(connection=connection)
    adapter.add(build_feature())
    assert adapter.features() == ["test_feature"]

def test_does_not_reconnect_a_callers_closed_connection(migrated_postgres_url, monkeypatch):
  monkeypatch.setenv("DATABASE_URL", migrated_postgres_url)
  connection = psycopg.connect(migrated_postgres_url, autocommit=True)
  adapter = PostgresAdapter(connection=connection)
  connection.close()
  with pytest.raises(psycopg.OperationalError):
    adapter.features()

def test_writes_join_the_callers_open_transaction(migrated_postgres_url):
  with psycopg.connect(migrated_postgres_url) as connection:
    adapter = PostgresAdapter(connection=connection)
    connection.execute("SELECT 1")  # opens the caller's transaction
    adapter.add(build_feature())
    connection.rollback()
    assert adapter.features() == []

def test_requires_a_database_url_or_connection(monkeypatch):
  monkeypatch.delenv("FEATURE_GATE_DATABASE_URL", raising=False)
  monkeypatch.delenv("DATABASE_URL", raising=False)
  with pytest.raises(ValueError):
    PostgresAdapter()
