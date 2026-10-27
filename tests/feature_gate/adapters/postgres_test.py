import uuid
import psycopg
import pytest
from feature_gate.client import Client, FeatureNotFound
from feature_gate.adapters.postgres import PostgresAdapter
from feature_gate.feature import Feature
from feature_gate.migrate import available_migrations, main

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

def test_table_prefix_defaults_to_feature_gate(client):
  assert client.adapter.table_prefix == "feature_gate_"

def test_custom_table_prefix_uses_its_own_table(migrated_postgres_url):
  main(["--database-url", migrated_postgres_url, "--table-prefix", "custom_ff_"])
  custom = PostgresAdapter(database_url=migrated_postgres_url, table_prefix="custom_ff_")
  default = PostgresAdapter(database_url=migrated_postgres_url)
  custom.add(build_feature("custom_only"))
  custom.enable("custom_only")
  assert custom.features() == ["custom_only"]
  assert custom.is_enabled("custom_only")
  assert default.features() == []
  with psycopg.connect(migrated_postgres_url) as connection:
    count = connection.execute("SELECT count(*) FROM custom_ff_features").fetchone()[0]
  assert count == 1
  custom.connection.close()
  default.connection.close()

def test_table_prefix_falls_back_to_env(migrated_postgres_url, monkeypatch):
  monkeypatch.setenv("FEATURE_GATE_TABLE_PREFIX", "custom_ff_")
  adapter = PostgresAdapter(database_url=migrated_postgres_url)
  assert adapter.table_prefix == "custom_ff_"
  adapter.connection.close()

@pytest.mark.parametrize("table_prefix", ["Feature_", "1ff_", "ff; DROP TABLE x; --", "a" * 47])
def test_rejects_unsafe_table_prefix(table_prefix):
  with pytest.raises(ValueError):
    PostgresAdapter(database_url="postgresql://unused", table_prefix=table_prefix)

def test_requires_a_database_url_or_connection(monkeypatch):
  monkeypatch.delenv("FEATURE_GATE_DATABASE_URL", raising=False)
  monkeypatch.delenv("DATABASE_URL", raising=False)
  with pytest.raises(ValueError):
    PostgresAdapter()

class User:
  def __init__(self, id):
    self.feature_gate_id = f"user:{id}"

def test_enable_actor_enables_feature_for_that_actor_only(client):
  client.add(build_feature())
  assert client.enable_actor("test_feature", "user:1")
  assert client.is_enabled("test_feature", "user:1")
  assert not client.is_enabled("test_feature", "user:2")
  assert not client.is_enabled("test_feature")

def test_is_enabled_when_any_actor_is_enabled(client):
  client.add(build_feature())
  client.enable_actor("test_feature", "org:7")
  assert client.is_enabled("test_feature", "user:1", "org:7")
  assert not client.is_enabled("test_feature", "user:1", "org:8")

def test_is_enabled_skips_none_actors(client):
  client.add(build_feature())
  client.enable_actor("test_feature", "user:1")
  assert client.is_enabled("test_feature", "user:1", None)
  assert not client.is_enabled("test_feature", None)

def test_globally_enabled_feature_is_enabled_for_every_actor(client):
  client.add(build_feature())
  client.enable("test_feature")
  assert client.is_enabled("test_feature", "user:2")

def test_disable_keeps_enabled_actors(client):
  client.add(build_feature())
  client.enable_actor("test_feature", "user:1")
  client.enable("test_feature")
  client.disable("test_feature")
  assert client.is_enabled("test_feature", "user:1")
  assert not client.is_enabled("test_feature", "user:2")

def test_disable_actor_disables_feature_for_that_actor(client):
  client.add(build_feature())
  client.enable_actor("test_feature", "user:1")
  assert client.disable_actor("test_feature", "user:1")
  assert not client.is_enabled("test_feature", "user:1")
  assert client.actors("test_feature") == []

def test_enable_and_disable_actor_are_idempotent(client):
  client.add(build_feature())
  assert client.enable_actor("test_feature", "user:1")
  assert client.enable_actor("test_feature", "user:1")
  assert client.actors("test_feature") == ["user:1"]
  assert client.disable_actor("test_feature", "user:1")
  assert client.disable_actor("test_feature", "user:1")
  assert client.actors("test_feature") == []

def test_actors_are_listed_in_the_order_added(client):
  client.add(build_feature())
  for actor in ["user:2", "org:7", "user:1"]:
    client.enable_actor("test_feature", actor)
  assert client.actors("test_feature") == ["user:2", "org:7", "user:1"]

def test_actors_are_scoped_to_their_feature(client):
  client.add(build_feature())
  client.add(build_feature("other_feature"))
  client.enable_actor("test_feature", "user:1")
  assert client.actors("other_feature") == []
  assert not client.is_enabled("other_feature", "user:1")

def test_actor_objects_use_their_feature_gate_id(client):
  client.add(build_feature())
  client.enable_actor("test_feature", User(1))
  assert client.actors("test_feature") == ["user:1"]
  assert client.is_enabled("test_feature", User(1))
  assert client.is_enabled("test_feature", "user:1")

def test_enable_actor_rejects_none(client):
  client.add(build_feature())
  with pytest.raises(TypeError):
    client.enable_actor("test_feature", None)

def test_remove_deletes_the_features_actors(client, migrated_postgres_url):
  client.add(build_feature())
  client.enable_actor("test_feature", "user:1")
  client.remove("test_feature")
  with psycopg.connect(migrated_postgres_url) as connection:
    count = connection.execute("SELECT count(*) FROM feature_gate_feature_actors").fetchone()[0]
  assert count == 0

def test_custom_table_prefix_uses_its_own_actors_table(migrated_postgres_url):
  main(["--database-url", migrated_postgres_url, "--table-prefix", "custom_ff_"])
  adapter = PostgresAdapter(database_url=migrated_postgres_url, table_prefix="custom_ff_")
  adapter.add(build_feature())
  adapter.enable_actor("test_feature", "user:1")
  with psycopg.connect(migrated_postgres_url) as connection:
    count = connection.execute("SELECT count(*) FROM custom_ff_feature_actors").fetchone()[0]
  assert count == 1
  adapter.connection.close()

def test_is_enabled_without_actors_works_before_the_actors_migration(postgres_url):
  _version, sql = available_migrations()[0]
  with psycopg.connect(postgres_url, autocommit=True) as connection:
    connection.execute(sql)
    connection.execute("INSERT INTO feature_gate_features (key, enabled) VALUES ('test_feature', true)")
  adapter = PostgresAdapter(database_url=postgres_url)
  assert adapter.is_enabled("test_feature")
  adapter.connection.close()

@pytest.mark.parametrize("call", [
  lambda client: client.enable_actor("test_feature", "user:1"),
  lambda client: client.disable_actor("test_feature", "user:1"),
  lambda client: client.actors("test_feature"),
  lambda client: client.is_enabled("test_feature", "user:1"),
])
def test_actor_methods_raise_when_feature_not_found(client, call):
  with pytest.raises(FeatureNotFound):
    call(client)
