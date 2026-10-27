from feature_gate.actor import actor_id, actor_ids
from feature_gate.client import FeatureNotFound
from feature_gate.clients.posthog_api_client import PosthogAPIClient

CATCH_ALL = {"properties": [], "rollout_percentage": None}

class PosthogAdapter:
  def __init__(self, api_key=None, project_id=None, logger=None):
    self.client = PosthogAPIClient(api_key=api_key, project_id=project_id, logger=logger)
    self.logger = self.client.logger

  def client(self):
    return self.client

  def logger(self):
    return self.logger

  def add(self, feature):
    if self.client.fetch_feature(feature.key) is None:
      self.client.create_feature(feature.key, feature.description)
    return True

  def remove(self, feature_key):
    if not self.client.fetch_feature(feature_key) is None:
      self.client.delete_feature(feature_key)
    return True

  def features(self):
    resp = self.client.list_features()
    key='key'
    return [item[key] for item in resp["data"] if key in item]

  # Actors are mapped onto the flag's release conditions. The adapter manages
  # two group shapes, the catch-all (everyone, i.e. the global switch) and one
  # actor group matching distinct_id, and leaves any other group untouched.

  def is_enabled(self, feature_key, *actors):
    ids = actor_ids(actors)
    feature = self._fetch_feature(feature_key)
    groups = self._groups(feature)
    actor_group = self._actor_group(groups)
    if actor_group is None:
      return feature["active"]
    return feature["active"] and (
      self._catch_all(groups) is not None or any(id in self._actor_values(actor_group) for id in ids)
    )

  def enable(self, feature_key):
    feature = self._fetch_feature(feature_key)
    groups = self._groups(feature)
    payload = {"active": True}
    if self._actor_group(groups) is not None and self._catch_all(groups) is None:
      payload["filters"] = self._filters(feature, groups + [dict(CATCH_ALL)])
    resp = self.client.update_feature(feature["id"], payload)
    return resp["data"]["active"]

  def disable(self, feature_key):
    feature = self._fetch_feature(feature_key)
    groups = self._groups(feature)
    if self._actor_group(groups) is None:
      payload = {"active": False}
    else:
      # Listed actors keep the flag, so it stays active without the catch-all.
      payload = {"active": True, "filters": self._filters(feature, [g for g in groups if not self._is_catch_all(g)])}
    resp = self.client.update_feature(feature["id"], payload)
    return resp["data"]["active"] == payload["active"]

  def enable_actor(self, feature_key, actor):
    id = actor_id(actor)
    feature = self._fetch_feature(feature_key)
    groups = self._groups(feature)
    if not feature["active"]:
      if any(not self._is_catch_all(g) and not self._is_actor_group(g) for g in groups):
        # Activating would also turn on conditions set up in PostHog.
        raise ValueError(f"Feature {feature_key} is inactive and has release conditions feature_gate doesn't manage; enable actors for it in PostHog.")
      # Globally off: activating with the catch-all would enable everyone.
      groups = [g for g in groups if not self._is_catch_all(g)]
    actor_group = self._actor_group(groups)
    if actor_group is None:
      groups.append(self._new_actor_group([id]))
    elif id not in self._actor_values(actor_group):
      index = groups.index(actor_group)
      groups[index] = self._new_actor_group(self._actor_values(actor_group) + [id])
    resp = self.client.update_feature(feature["id"], {"active": True, "filters": self._filters(feature, groups)})
    return resp["data"]["active"]

  def disable_actor(self, feature_key, actor):
    id = actor_id(actor)
    feature = self._fetch_feature(feature_key)
    groups = self._groups(feature)
    actor_group = self._actor_group(groups)
    if actor_group is None or id not in self._actor_values(actor_group):
      return True
    values = [value for value in self._actor_values(actor_group) if value != id]
    index = groups.index(actor_group)
    payload = {}
    if values:
      groups[index] = self._new_actor_group(values)
    else:
      del groups[index]
      if self._catch_all(groups) is None:
        # The last actor was the only thing keeping a globally-off flag
        # active; restore the default shape so enable() works as before.
        groups.append(dict(CATCH_ALL))
        payload["active"] = False
    payload["filters"] = self._filters(feature, groups)
    resp = self.client.update_feature(feature["id"], payload)
    return "data" in resp

  def actors(self, feature_key):
    feature = self._fetch_feature(feature_key)
    actor_group = self._actor_group(self._groups(feature))
    return [] if actor_group is None else self._actor_values(actor_group)

  def _fetch_feature(self, feature_key):
    feature = self.client.fetch_feature(feature_key)
    if feature is None:
      raise FeatureNotFound(f"Feature {feature_key} not found")
    return feature

  def _groups(self, feature):
    return list((feature.get("filters") or {}).get("groups") or [])

  def _filters(self, feature, groups):
    # PATCH replaces filters wholesale, so keep payloads, variants, etc.
    return {**(feature.get("filters") or {}), "groups": groups}

  def _is_catch_all(self, group):
    return not group.get("properties") and group.get("rollout_percentage") in (None, 100)

  def _is_actor_group(self, group):
    properties = group.get("properties") or []
    return (
      len(properties) == 1
      and properties[0].get("key") == "distinct_id"
      and properties[0].get("operator") == "exact"
      and isinstance(properties[0].get("value"), list)
      and group.get("rollout_percentage") in (None, 100)
    )

  def _catch_all(self, groups):
    return next((g for g in groups if self._is_catch_all(g)), None)

  def _actor_group(self, groups):
    return next((g for g in groups if self._is_actor_group(g)), None)

  def _actor_values(self, actor_group):
    return list(actor_group["properties"][0]["value"])

  def _new_actor_group(self, ids):
    return {
      "properties": [{"key": "distinct_id", "type": "person", "operator": "exact", "value": ids}],
      "rollout_percentage": 100,
    }

  # def enable_expression(self, expression):
  #   raise NotImplementedError

  # def disable_expression(self, expression):
  #   raise NotImplementedError

  # def expression(self):
  #   raise NotImplementedError

  # def add_expression(self, expression):
  #   raise NotImplementedError

  # def remove_expression(self, expression):
  #   raise NotImplementedError

  # def enable_group(self, feature, group):
  #   raise NotImplementedError

  # def disable_group(self, feature, group):
  #   raise NotImplementedError

  # def enable_percentage_of_actors(self, feature, percentage):
  #   raise NotImplementedError

  # def disable_percentage_of_actors(self, feature, percentage):
  #   raise NotImplementedError

  # def enable_percentage_of_time(self, feature, percentage):
  #   raise NotImplementedError

  # def disable_percentage_of_time(self, feature, percentage):
  #   raise NotImplementedError

  # def feature(self):
  #   raise NotImplementedError

  # # def [](self):
  # #   raise NotImplementedError

  # def preload(self):
  #   raise NotImplementedError

  # def preload_all(self):
  #   raise NotImplementedError

  # def adapter(self):
  #   raise NotImplementedError

  # def do_import(self):
  #   raise NotImplementedError

  # def do_export(self):
  #   raise NotImplementedError

  # def memoize(self):
  #   raise NotImplementedError

  # def is_memorizing(self):
  #   raise NotImplementedError

  # def is_read_only(self):
  #   raise NotImplementedError

  # def sync(self):
  #   raise NotImplementedError

  # def sync_secret(self):
  #   raise NotImplementedError
