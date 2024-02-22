class FeatureNotFound(ValueError):
  pass

class Client:
  def __init__(self, adapter):
    self.adapter = adapter

  def adapter(self):
    return self.adapter

  def add(self, feature):
    return self.adapter.add(feature)

  def remove(self, feature):
    return self.adapter.remove(feature)

  def features(self):
    return self.adapter.features()

  def is_enabled(self, feature):
    return self.adapter.is_enabled(feature)

  def enable(self, feature):
    return self.adapter.enable(feature)

  def disable(self, feature):
    return self.adapter.disable(feature)

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

  # def enable_actor(self, feature, actor):
  #   raise NotImplementedError

  # def disable_actor(self, feature, actor):
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
