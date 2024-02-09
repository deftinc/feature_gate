import typing
from pymongo.collection import Collection
from pymongo.cursor import Cursor

class MongoAdapter:
  def __init__(self, collection: Collection):
    self.collection: Collection = collection
    self.features_key: str = '__featuregate_internals__'

  def is_enabled(self, feature: str, actor) -> bool:
    raise NotImplementedError

  def enable(self, feature: str) -> None:
    raise NotImplementedError

  def disable(self, feature: str) -> None:
    raise NotImplementedError

  def enable_expression(self, expression):
    raise NotImplementedError

  def disable_expression(self, expression):
    raise NotImplementedError

  def expression(self):
    raise NotImplementedError

  def add_expression(self, expression):
    raise NotImplementedError

  def remove_expression(self, expression):
    raise NotImplementedError

  def enable_actor(self, feature: str, actor):
    raise NotImplementedError

  def disable_actor(self, feature: str, actor):
    raise NotImplementedError

  def enable_group(self, feature: str, group):
    raise NotImplementedError

  def disable_group(self, feature: str, group):
    raise NotImplementedError

  def enable_percentage_of_actors(self, feature: str, percentage: int):
    raise NotImplementedError

  def disable_percentage_of_actors(self, feature: str, percentage: int):
    raise NotImplementedError

  def enable_percentage_of_time(self, feature: str, percentage: int):
    raise NotImplementedError

  def disable_percentage_of_time(self, feature: str, percentage: int):
    raise NotImplementedError

  def features(self) -> typing.List[str]:
    return self._read_feature_keys()['features']

  def feature(self):
    raise NotImplementedError

  # def [](self):
  #   raise NotImplementedError

  def preload(self):
    raise NotImplementedError

  def preload_all(self):
    raise NotImplementedError

  def adapter(self):
    raise NotImplementedError

  def add(self, feature) -> bool:
    self._update(self.features_key, {'$addToSet': {'features': feature.key}})
    return True

  def remove(self, feature) -> bool:
    self._update(self.features_key, {'$pull': {'features': feature.key}})
    self.clear(feature)
    return True

  def clear(self, feature):
    self._delete(feature.key)
    return True

  def do_import(self):
    raise NotImplementedError

  def do_export(self):
    raise NotImplementedError

  def memoize(self):
    raise NotImplementedError

  def is_memorizing(self):
    raise NotImplementedError

  def is_read_only(self):
    raise NotImplementedError

  def sync(self):
    raise NotImplementedError

  def sync_secret(self):
    raise NotImplementedError

  def _read_feature_keys(self) -> Cursor:
    return self.collection.find_one({'_id': self.features_key})

  def _update(self, key: str, updates):
    return self.collection.update_one({'_id': key}, updates, upsert=True)

  def _delete(self, key: str):
    return self.collection.delete_one({'_id': key})

# def _result_for_feature(feature, doc):
#   result = {}
#   for gate: str in feature.gates
#     result[gate] = case type(gate)
#       when int or bool:
#         doc[gate]
#       when hash:
#         doc.fetch(gate)
