import structlog
from pathlib import Path
from feature_gate.client import FeatureNotFound

from structlog.contextvars import (
    bind_contextvars,
    merge_contextvars,
    bound_contextvars,
)

class MemoryAdapter:
  def __init__(self):
    self._features = []
    bind_contextvars(klass="MemoryAdapter")
    log_path = Path("logs").joinpath("feature_gate").with_suffix(".log")
    Path.mkdir(Path("logs"), exist_ok=True)
    Path.touch(log_path)
    structlog.configure(
      processors=[
        merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
      ],
      logger_factory=structlog.WriteLoggerFactory(
        file=log_path.open("wt")
      ),
    )
    self._logger = structlog.get_logger()

  def add(self, feature):
    self._logger.info("Add feature key={feature.key}")
    if feature.key not in self._features:
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
    self._logger.info("Remove feature key={feature.key}")
    for feature in self._features:
      if feature["key"] == feature_key:
        self._features.remove(feature)
        return True
    raise FeatureNotFound("Feature {feature_key} not found.")

  def features(self):
    features = [feature["key"] for feature in self._features]
    self._logger.info("Lists features {features}")
    return features

  def is_enabled(self, feature_key):
    for feature in self._features:
      if feature["key"] == feature_key:
        is_enabled = feature["gates"]["boolean"]["enabled"]
        self._logger.info("Check feature key={feature.key} enabled={is_enabled}")
        return is_enabled
    raise FeatureNotFound("Feature {feature_key} not found.")

  def enable(self, feature_key):
    self._logger.info("Enable feature key={feature.key}")
    for feature in self._features:
      if feature["key"] == feature_key:
        feature["gates"]["boolean"]["enabled"] = True
        return True
    raise FeatureNotFound("Feature {feature_key} not found.")

  def disable(self, feature_key):
    self._logger.info("Disable feature key={feature.key}")
    for feature in self._features:
      if feature["key"] == feature_key:
        feature["gates"]["boolean"]["enabled"] = False
        return True
    raise FeatureNotFound("Feature {feature_key} not found.")
