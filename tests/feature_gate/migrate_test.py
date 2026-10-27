import uuid
import psycopg
import pytest
from feature_gate.migrate import MigrationError, available_migrations, main, migrate

def table_names(url, table_prefix="feature_gate_"):
  with psycopg.connect(url) as connection:
    rows = connection.execute(
      "SELECT table_name FROM information_schema.tables WHERE starts_with(table_name, %s)",
      (table_prefix,),
    ).fetchall()
  return {row[0] for row in rows}

def function_exists(url, name):
  with psycopg.connect(url) as connection:
    return connection.execute("SELECT to_regproc(%s) IS NOT NULL", (name,)).fetchone()[0]

def test_available_migrations_are_packaged_and_ordered():
  versions = [version for version, _sql in available_migrations()]
  assert versions[0] == "0001_create_features"
  assert versions == sorted(versions)

def test_migrate_creates_tables(postgres_url):
  assert table_names(postgres_url) == set()
  with psycopg.connect(postgres_url, autocommit=True) as connection:
    applied = migrate(connection)
  assert applied == [version for version, _sql in available_migrations()]
  assert table_names(postgres_url) == {"feature_gate_features", "feature_gate_feature_actors", "feature_gate_schema_migrations"}

def test_uuidv7_function_sets_version_variant_and_timestamp(postgres_url):
  with psycopg.connect(postgres_url, autocommit=True) as connection:
    migrate(connection)
    id, now_ms = connection.execute(
      "SELECT feature_gate_uuidv7(), (extract(epoch FROM clock_timestamp()) * 1000)::bigint"
    ).fetchone()
  assert id.version == 7
  assert id.variant == uuid.RFC_4122
  assert abs((id.int >> 80) - now_ms) < 1000

def test_migrate_with_custom_table_prefix(postgres_url):
  with psycopg.connect(postgres_url, autocommit=True) as connection:
    applied = migrate(connection, table_prefix="custom_ff_")
    id = connection.execute("SELECT custom_ff_uuidv7()").fetchone()[0]
  assert applied == [version for version, _sql in available_migrations()]
  assert table_names(postgres_url, "custom_ff_") == {"custom_ff_features", "custom_ff_feature_actors", "custom_ff_schema_migrations"}
  assert table_names(postgres_url) == set()
  assert not function_exists(postgres_url, "feature_gate_uuidv7")
  assert id.version == 7

def test_prefixes_have_separate_migration_histories(postgres_url):
  with psycopg.connect(postgres_url, autocommit=True) as connection:
    migrate(connection)
    assert migrate(connection, table_prefix="custom_ff_") != []
    assert migrate(connection, table_prefix="custom_ff_") == []

def test_available_migrations_substitute_the_prefix():
  for _version, sql in available_migrations("custom_ff_"):
    assert "{prefix}" not in sql
    assert "feature_gate_" not in sql

def test_migrate_rejects_unsafe_table_prefix(postgres_url):
  with psycopg.connect(postgres_url, autocommit=True) as connection:
    with pytest.raises(ValueError):
      migrate(connection, table_prefix="ff; DROP TABLE x; --")

def test_main_reads_table_prefix_from_flag_and_env(postgres_url, monkeypatch):
  assert main(["--database-url", postgres_url, "--table-prefix", "custom_ff_"]) == 0
  assert table_names(postgres_url, "custom_ff_") == {"custom_ff_features", "custom_ff_feature_actors", "custom_ff_schema_migrations"}
  monkeypatch.setenv("FEATURE_GATE_TABLE_PREFIX", "custom_ff_")
  assert main(["--database-url", postgres_url]) == 0
  assert table_names(postgres_url) == set()

def test_main_errors_on_unsafe_table_prefix(postgres_url):
  with pytest.raises(SystemExit):
    main(["--database-url", postgres_url, "--table-prefix", "Bad-Prefix"])

def test_migrate_is_a_noop_when_up_to_date(postgres_url):
  with psycopg.connect(postgres_url, autocommit=True) as connection:
    migrate(connection)
    assert migrate(connection) == []

def test_migrate_requires_autocommit(postgres_url):
  with psycopg.connect(postgres_url) as connection:
    with pytest.raises(MigrationError):
      migrate(connection)

def test_main_reads_database_url_from_env(postgres_url, monkeypatch, capsys):
  monkeypatch.delenv("DATABASE_URL", raising=False)
  monkeypatch.setenv("FEATURE_GATE_DATABASE_URL", postgres_url)
  assert main([]) == 0
  assert "Applied 0001_create_features" in capsys.readouterr().out
  assert main([]) == 0
  assert "No pending migrations." in capsys.readouterr().out

def test_main_errors_without_database_url(monkeypatch):
  monkeypatch.delenv("FEATURE_GATE_DATABASE_URL", raising=False)
  monkeypatch.delenv("DATABASE_URL", raising=False)
  with pytest.raises(SystemExit):
    main([])
