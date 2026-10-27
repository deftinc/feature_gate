-- Actors (e.g. "user:42", "org:7") a feature is enabled for, in addition to
-- its global enabled switch.
CREATE TABLE {prefix}feature_actors (
  id uuid PRIMARY KEY DEFAULT {prefix}uuidv7(),
  feature_id uuid NOT NULL REFERENCES {prefix}features (id) ON DELETE CASCADE,
  actor_id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (feature_id, actor_id)
);
