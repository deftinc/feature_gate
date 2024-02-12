class Feature:
  def __init__(self, name, key, description, adapter, instrumenter):
    self._name = name
    self._key = key
    self._description = description
    self._adapter = adapter
    self._instrumenter = instrumenter

  @property
  def name(self):
    return self._name

  @property
  def key(self):
    return self._key

  @property
  def description(self):
    return self._description

  @property
  def adapter(self):
    return self._adapter

  @property
  def instrumenter(self):
    return self._instrumenter
