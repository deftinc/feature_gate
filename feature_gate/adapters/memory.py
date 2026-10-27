import structlog
from feature_gate.actor import actor_id, actor_ids
from feature_gate.client import FeatureNotFound

from structlog.contextvars import (
    bind_contextvars,
    merge_contextvars,
    bound_contextvars,
)

class MemoryAdapter:
  def __init__(self, logger=None):
    self._features = []
    bind_contextvars(klass="MemoryAdapter")
    self.logger = logger or structlog.get_logger()

  def logger(self):
    return self.logger

  def add(self, feature):
    if feature.key not in self.features():
      self._features.append({
        "name": feature.name,
        "key": feature.key,
        "description": feature.description,
        "gates": {
          "boolean": {
            "enabled": False
          },
          "actors": []
        }
      })
    return True

  def remove(self, feature_key):
    for feature in self._features:
      if feature["key"] == feature_key:
        self._features.remove(feature)
        return True
    raise FeatureNotFound(f"Feature {feature_key} not found.")

  def features(self):
    features = [feature["key"] for feature in self._features]
    return features

  def is_enabled(self, feature_key, *actors):
    ids = actor_ids(actors)
    for feature in self._features:
      if feature["key"] == feature_key:
        gates = feature["gates"]
        is_enabled = gates["boolean"]["enabled"] or any(id in gates["actors"] for id in ids)
        return is_enabled
    raise FeatureNotFound(f"Feature {feature_key} not found.")

  def enable(self, feature_key):
    for feature in self._features:
      if feature["key"] == feature_key:
        feature["gates"]["boolean"]["enabled"] = True
        return True
    raise FeatureNotFound(f"Feature {feature_key} not found.")

  def disable(self, feature_key):
    for feature in self._features:
      if feature["key"] == feature_key:
        feature["gates"]["boolean"]["enabled"] = False
        return True
    raise FeatureNotFound(f"Feature {feature_key} not found.")

  def enable_actor(self, feature_key, actor):
    id = actor_id(actor)
    for feature in self._features:
      if feature["key"] == feature_key:
        if id not in feature["gates"]["actors"]:
          feature["gates"]["actors"].append(id)
        return True
    raise FeatureNotFound(f"Feature {feature_key} not found.")

  def disable_actor(self, feature_key, actor):
    id = actor_id(actor)
    for feature in self._features:
      if feature["key"] == feature_key:
        if id in feature["gates"]["actors"]:
          feature["gates"]["actors"].remove(id)
        return True
    raise FeatureNotFound(f"Feature {feature_key} not found.")

  def actors(self, feature_key):
    for feature in self._features:
      if feature["key"] == feature_key:
        return list(feature["gates"]["actors"])
    raise FeatureNotFound(f"Feature {feature_key} not found.")
