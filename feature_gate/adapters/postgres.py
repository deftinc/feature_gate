import structlog
from feature_gate.actor import actor_id, actor_ids
from feature_gate.client import FeatureNotFound
from feature_gate.migrate import database_url_from_env, table_prefix_from_env, validate_table_prefix

from structlog.contextvars import bind_contextvars

class PostgresAdapter:
  """Stores features in the <table_prefix>features table and the actors they
  are enabled for in <table_prefix>feature_actors.

  Run `feature-gate-migrate` against the database, with the same table prefix,
  before using this adapter. `table_prefix` falls back to
  $FEATURE_GATE_TABLE_PREFIX, then "feature_gate_".
  Pass either a `database_url` (falls back to $FEATURE_GATE_DATABASE_URL, then
  $DATABASE_URL) or an existing psycopg `connection`. With a non-autocommit
  connection that is already inside a transaction, writes join that transaction
  and are committed when the caller commits.
  `logger` defaults to `structlog.get_logger()`, which follows the host's
  structlog configuration.
  """
  def __init__(self, database_url=None, connection=None, table_prefix=None, logger=None):
    import psycopg

    self._psycopg = psycopg
    self.table_prefix = validate_table_prefix(table_prefix or table_prefix_from_env())
    self._table = f"{self.table_prefix}features"
    self._actors_table = f"{self.table_prefix}feature_actors"
    # Only fall back to the env when no connection is given, so a closed
    # caller-owned connection raises instead of reconnecting elsewhere.
    self.database_url = database_url or (database_url_from_env() if connection is None else None)
    if connection is None and not self.database_url:
      raise ValueError("PostgresAdapter needs a database_url, a connection, or FEATURE_GATE_DATABASE_URL/DATABASE_URL")
    self.connection = connection or psycopg.connect(self.database_url, autocommit=True)
    bind_contextvars(klass="PostgresAdapter")
    self.logger = logger or structlog.get_logger()

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

  def is_enabled(self, feature_key, *actors):
    ids = actor_ids(actors)
    if not ids:
      # Only touches the features table, so plain checks keep working for
      # apps that upgrade before migrating the actors table.
      rows = self._query(
        f"SELECT enabled FROM {self._table} WHERE key = %s",
        (feature_key,),
      )
    else:
      rows = self._query(
        f"""
        SELECT f.enabled OR EXISTS (
          SELECT 1 FROM {self._actors_table} a
          WHERE a.feature_id = f.id AND a.actor_id = ANY(%s::text[])
        )
        FROM {self._table} f
        WHERE f.key = %s
        """,
        (ids, feature_key),
      )
    self._raise_if_missing(rows, feature_key)
    return rows[0][0]

  def enable(self, feature_key):
    self._set_enabled(feature_key, True)
    return True

  def disable(self, feature_key):
    self._set_enabled(feature_key, False)
    return True

  def enable_actor(self, feature_key, actor):
    # Data-modifying CTEs always run; selecting the feature id tells a missing
    # feature apart from an actor that was already enabled.
    rows = self._query(
      f"""
      WITH feature AS (SELECT id FROM {self._table} WHERE key = %s),
      inserted AS (
        INSERT INTO {self._actors_table} (feature_id, actor_id)
        SELECT id, %s FROM feature
        ON CONFLICT (feature_id, actor_id) DO NOTHING
      )
      SELECT id FROM feature
      """,
      (feature_key, actor_id(actor)),
    )
    self._raise_if_missing(rows, feature_key)
    return True

  def disable_actor(self, feature_key, actor):
    rows = self._query(
      f"""
      WITH feature AS (SELECT id FROM {self._table} WHERE key = %s),
      deleted AS (
        DELETE FROM {self._actors_table} a
        USING feature
        WHERE a.feature_id = feature.id AND a.actor_id = %s
      )
      SELECT id FROM feature
      """,
      (feature_key, actor_id(actor)),
    )
    self._raise_if_missing(rows, feature_key)
    return True

  def actors(self, feature_key):
    rows = self._query(
      f"""
      SELECT a.actor_id
      FROM {self._table} f
      LEFT JOIN {self._actors_table} a ON a.feature_id = f.id
      WHERE f.key = %s
      ORDER BY a.id
      """,
      (feature_key,),
    )
    self._raise_if_missing(rows, feature_key)
    return [row[0] for row in rows if row[0] is not None]

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
