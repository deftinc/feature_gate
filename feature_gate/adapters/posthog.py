from feature_gate.clients.posthog_api_client import PosthogAPIClient
class PosthogAdapter:
  def __init__(self, api_key, project_id):
    self.client = PosthogAPIClient(api_key=api_key, project_id=project_id)

  def client(self):
    return self.client

  def add(self, feature):
    if self.client.fetch_feature(feature.key) == None:
      self.client.create_feature(feature.key, feature.description)
    return True

  def remove(self, feature_key):
    return self.client.delete_feature(feature_key)

  def features(self):
    resp = self.client.list_features()
    key='key'
    return [item[key] for item in resp["data"] if key in item]

  def is_enabled(self, feature_key):
    return self.client.is_enabled(feature_key)

  def enable(self, feature_key):
    return self.client.enable_feature(feature_key)

  def disable(self, feature_key):
    return self.client.disable_feature(feature_key)

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
