import structlog
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
          }
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

  def is_enabled(self, feature_key):
    for feature in self._features:
      if feature["key"] == feature_key:
        is_enabled = feature["gates"]["boolean"]["enabled"]
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
