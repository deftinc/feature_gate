class PosthogAdapter:
  def __init__(self, collection):
    raise NotImplementedError

  def is_enabled(self, feature, actor):
    raise NotImplementedError

  def enable(self, feature):
    raise NotImplementedError

  def disable(self, feature):
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

  def enable_actor(self, feature, actor):
    raise NotImplementedError

  def disable_actor(self, feature, actor):
    raise NotImplementedError

  def enable_group(self, feature, group):
    raise NotImplementedError

  def disable_group(self, feature, group):
    raise NotImplementedError

  def enable_percentage_of_actors(self, feature, percentage):
    raise NotImplementedError

  def disable_percentage_of_actors(self, feature, percentage):
    raise NotImplementedError

  def enable_percentage_of_time(self, feature, percentage):
    raise NotImplementedError

  def disable_percentage_of_time(self, feature, percentage):
    raise NotImplementedError

  def features(self):
    raise NotImplementedError

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

  def add(self):
    raise NotImplementedError

  def remove(self):
    raise NotImplementedError

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
