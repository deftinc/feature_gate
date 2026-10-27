def actor_id(actor):
  """The id a flag is enabled for: a string the caller namespaces ("user:42",
  "org:7"), or any object with a `feature_gate_id` attribute.

  Bare ints are rejected so user 42 and org 42 can't collide.
  """
  if isinstance(actor, str):
    id = actor
  elif hasattr(actor, "feature_gate_id"):
    id = str(actor.feature_gate_id)
  else:
    raise TypeError(f"Actor {actor!r} must be a string or have a feature_gate_id attribute.")
  if not id:
    raise ValueError(f"Actor {actor!r} has an empty id.")
  return id

def actor_ids(actors):
  """Resolves the actors passed to is_enabled, skipping None (e.g. a user with no org)."""
  return [actor_id(actor) for actor in actors if actor is not None]
