class Feature:
  def __init__(self, name, key, description):
    self._name = name
    self._key = key
    self._description = description

  @property
  def name(self):
    return self._name

  @property
  def key(self):
    return self._key

  @property
  def description(self):
    return self._description

  def __repr__(self):
    return f"Feature(name={self._name!r}, key={self._key!r}, description={self._description!r})"
