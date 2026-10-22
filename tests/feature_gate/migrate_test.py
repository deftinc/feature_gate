import psycopg
import pytest
from feature_gate.migrate import MigrationError, available_migrations, main, migrate

def table_names(url):
  with psycopg.connect(url) as connection:
    rows = connection.execute(
      "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'feature_gate_%'"
    ).fetchall()
  return {row[0] for row in rows}

def test_available_migrations_are_packaged_and_ordered():
  versions = [version for version, _sql in available_migrations()]
  assert versions[0] == "0001_create_feature_gate_features"
  assert versions == sorted(versions)

def test_migrate_creates_tables(postgres_url):
  assert table_names(postgres_url) == set()
  with psycopg.connect(postgres_url, autocommit=True) as connection:
    applied = migrate(connection)
  assert applied == [version for version, _sql in available_migrations()]
  assert table_names(postgres_url) == {"feature_gate_features", "feature_gate_schema_migrations"}

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
  assert "Applied 0001_create_feature_gate_features" in capsys.readouterr().out
  assert main([]) == 0
  assert "No pending migrations." in capsys.readouterr().out

def test_main_errors_without_database_url(monkeypatch):
  monkeypatch.delenv("FEATURE_GATE_DATABASE_URL", raising=False)
  monkeypatch.delenv("DATABASE_URL", raising=False)
  with pytest.raises(SystemExit):
    main([])
