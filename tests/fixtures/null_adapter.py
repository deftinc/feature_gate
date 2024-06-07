class NullAdapter:
  def __init__(self):
    self.logger = NullLogger()

  def logger(self):
    return self.logger

  def add(self, feature):
    pass

  def remove(self, feature_key):
    pass

  def features(self):
    pass

  def is_enabled(self, feature_key):
    pass

  def enable(self, feature_key):
    pass

  def disable(self, feature_key):
    pass

class NullLogger:
  def __init__(self):
    pass

  def info(self, msg, *args, **kwargs):
    print("INFO: ", msg % tuple(args), " ".join(f"{k}={v}" for k, v in kwargs.items()))
