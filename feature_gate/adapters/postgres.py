import structlog
from feature_gate.client import FeatureNotFound
from feature_gate.migrate import database_url_from_env, table_prefix_from_env, validate_table_prefix

from structlog.contextvars import bind_contextvars

class PostgresAdapter:
  """Stores features in the <table_prefix>features table.

  Run `feature-gate-migrate` against the database, with the same table prefix,
  before using this adapter. `table_prefix` falls back to
  $FEATURE_GATE_TABLE_PREFIX, then "feature_gate_".
  Pass either a `database_url` (falls back to $FEATURE_GATE_DATABASE_URL, then
  $DATABASE_URL) or an existing psycopg `connection`. With a non-autocommit
  connection that is already inside a transaction, writes join that transaction
  and are committed when the caller commits.
  """
  def __init__(self, database_url=None, connection=None, table_prefix=None):
    import psycopg

    self._psycopg = psycopg
    self.table_prefix = validate_table_prefix(table_prefix or table_prefix_from_env())
    self._table = f"{self.table_prefix}features"
    # Only fall back to the env when no connection is given, so a closed
    # caller-owned connection raises instead of reconnecting elsewhere.
    self.database_url = database_url or (database_url_from_env() if connection is None else None)
    if connection is None and not self.database_url:
      raise ValueError("PostgresAdapter needs a database_url, a connection, or FEATURE_GATE_DATABASE_URL/DATABASE_URL")
    self.connection = connection or psycopg.connect(self.database_url, autocommit=True)
    bind_contextvars(klass="PostgresAdapter")
    self.logger = structlog.get_logger()

  def connection(self):
    return self.connection

  def table_prefix(self):
    return self.table_prefix

  def logger(self):
    return self.logger

  def add(self, feature):
    self._query(
      f"""
      INSERT INTO {self._table} (key, name, description)
      VALUES (%s, %s, %s)
      ON CONFLICT (key) DO NOTHING
      """,
      (feature.key, feature.name, feature.description),
    )
    return True

  def remove(self, feature_key):
    rows = self._query(
      f"DELETE FROM {self._table} WHERE key = %s RETURNING id",
      (feature_key,),
    )
    self._raise_if_missing(rows, feature_key)
    return True

  def features(self):
    rows = self._query(f"SELECT key FROM {self._table} ORDER BY id")
    return [row[0] for row in rows]

  def is_enabled(self, feature_key):
    rows = self._query(
      f"SELECT enabled FROM {self._table} WHERE key = %s",
      (feature_key,),
    )
    self._raise_if_missing(rows, feature_key)
    return rows[0][0]

  def enable(self, feature_key):
    self._set_enabled(feature_key, True)
    return True

  def disable(self, feature_key):
    self._set_enabled(feature_key, False)
    return True

  def _set_enabled(self, feature_key, enabled):
    rows = self._query(
      f"""
      UPDATE {self._table}
      SET enabled = %s, updated_at = now()
      WHERE key = %s
      RETURNING id
      """,
      (enabled, feature_key),
    )
    self._raise_if_missing(rows, feature_key)

  def _raise_if_missing(self, rows, feature_key):
    if not rows:
      raise FeatureNotFound(f"Feature {feature_key} not found.")

  def _query(self, sql, params=None):
    if self.connection.closed and self.database_url:
      self.connection = self._psycopg.connect(self.database_url, autocommit=True)
    with self.connection.transaction():
      cursor = self.connection.execute(sql, params)
      return cursor.fetchall() if cursor.description else []
