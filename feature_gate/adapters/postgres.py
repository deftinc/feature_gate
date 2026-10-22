import structlog
from feature_gate.client import FeatureNotFound
from feature_gate.migrate import database_url_from_env

from structlog.contextvars import bind_contextvars

class PostgresAdapter:
  """Stores features in the feature_gate_features table.

  Run `feature-gate-migrate` against the database before using this adapter.
  Pass either a `database_url` (falls back to $FEATURE_GATE_DATABASE_URL, then
  $DATABASE_URL) or an existing psycopg `connection`. With a non-autocommit
  connection that is already inside a transaction, writes join that transaction
  and are committed when the caller commits.
  """
  def __init__(self, database_url=None, connection=None):
    import psycopg

    self._psycopg = psycopg
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

  def logger(self):
    return self.logger

  def add(self, feature):
    self._query(
      """
      INSERT INTO feature_gate_features (key, name, description)
      VALUES (%s, %s, %s)
      ON CONFLICT (key) DO NOTHING
      """,
      (feature.key, feature.name, feature.description),
    )
    return True

  def remove(self, feature_key):
    rows = self._query(
      "DELETE FROM feature_gate_features WHERE key = %s RETURNING id",
      (feature_key,),
    )
    self._raise_if_missing(rows, feature_key)
    return True

  def features(self):
    rows = self._query("SELECT key FROM feature_gate_features ORDER BY id")
    return [row[0] for row in rows]

  def is_enabled(self, feature_key):
    rows = self._query(
      "SELECT enabled FROM feature_gate_features WHERE key = %s",
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
      """
      UPDATE feature_gate_features
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
