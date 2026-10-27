import pytest
from feature_gate.client import Client, FeatureNotFound
from feature_gate.adapters.memory import MemoryAdapter
from feature_gate.feature import Feature

def configured_client():
  adapter = MemoryAdapter()
  return Client(adapter)

def build_feature():
  return Feature("test_feature", "test_feature", "This is a test feature")

def test_client_initialization():
  client = configured_client()
  assert isinstance(client.adapter, MemoryAdapter)

def test_add_feature():
  client = configured_client()
  feature = build_feature()
  assert client.add(feature)
  features = client.features()
  assert "test_feature" in features

def test_remove_feature():
  client = configured_client()
  feature = build_feature()
  client.add(feature)
  features = client.features()
  assert "test_feature" in features
  assert client.remove("test_feature")
  features = client.features()
  assert "test_feature" not in features

def test_enable_feature():
  client = configured_client()
  feature = build_feature()
  client.add(feature)
  features = client.features()
  assert "test_feature" in features
  assert client.enable("test_feature")

def test_is_enabled_feature():
  client = configured_client()
  feature = build_feature()
  client.add(feature)
  assert not client.is_enabled("test_feature")
  assert client.enable("test_feature")
  assert client.is_enabled("test_feature")

def test_is_enabled_feature_not_found():
  client = configured_client()
  with pytest.raises(FeatureNotFound):
    client.is_enabled("test_feature")

def test_enable_feature_not_found():
  client = configured_client()
  with pytest.raises(FeatureNotFound):
    client.enable("test_feature")

def test_disable_feature_not_found():
  client = configured_client()
  with pytest.raises(FeatureNotFound):
    client.disable("test_feature")

def test_remove_feature_not_found():
  client = configured_client()
  with pytest.raises(FeatureNotFound):
    client.remove("test_feature")

def test_add_feature_twice_does_not_duplicate():
  client = configured_client()
  feature = build_feature()
  assert client.add(feature)
  assert client.add(feature)
  assert client.features() == ["test_feature"]

def test_feature_not_found_message_includes_key():
  client = configured_client()
  with pytest.raises(FeatureNotFound, match="Feature test_feature not found."):
    client.is_enabled("test_feature")

class User:
  def __init__(self, id):
    self.feature_gate_id = f"user:{id}"

def test_enable_actor_enables_feature_for_that_actor_only():
  client = configured_client()
  client.add(build_feature())
  assert client.enable_actor("test_feature", "user:1")
  assert client.is_enabled("test_feature", "user:1")
  assert not client.is_enabled("test_feature", "user:2")
  assert not client.is_enabled("test_feature")

def test_is_enabled_when_any_actor_is_enabled():
  client = configured_client()
  client.add(build_feature())
  client.enable_actor("test_feature", "org:7")
  assert client.is_enabled("test_feature", "user:1", "org:7")
  assert not client.is_enabled("test_feature", "user:1", "org:8")

def test_is_enabled_skips_none_actors():
  client = configured_client()
  client.add(build_feature())
  client.enable_actor("test_feature", "user:1")
  assert client.is_enabled("test_feature", "user:1", None)
  assert not client.is_enabled("test_feature", None)

def test_globally_enabled_feature_is_enabled_for_every_actor():
  client = configured_client()
  client.add(build_feature())
  client.enable("test_feature")
  assert client.is_enabled("test_feature", "user:2")

def test_disable_keeps_enabled_actors():
  client = configured_client()
  client.add(build_feature())
  client.enable_actor("test_feature", "user:1")
  client.enable("test_feature")
  client.disable("test_feature")
  assert client.is_enabled("test_feature", "user:1")
  assert not client.is_enabled("test_feature", "user:2")

def test_disable_actor_disables_feature_for_that_actor():
  client = configured_client()
  client.add(build_feature())
  client.enable_actor("test_feature", "user:1")
  assert client.disable_actor("test_feature", "user:1")
  assert not client.is_enabled("test_feature", "user:1")
  assert client.actors("test_feature") == []

def test_enable_and_disable_actor_are_idempotent():
  client = configured_client()
  client.add(build_feature())
  assert client.enable_actor("test_feature", "user:1")
  assert client.enable_actor("test_feature", "user:1")
  assert client.actors("test_feature") == ["user:1"]
  assert client.disable_actor("test_feature", "user:1")
  assert client.disable_actor("test_feature", "user:1")
  assert client.actors("test_feature") == []

def test_actors_are_listed_in_the_order_added():
  client = configured_client()
  client.add(build_feature())
  for actor in ["user:2", "org:7", "user:1"]:
    client.enable_actor("test_feature", actor)
  assert client.actors("test_feature") == ["user:2", "org:7", "user:1"]

def test_actor_objects_use_their_feature_gate_id():
  client = configured_client()
  client.add(build_feature())
  client.enable_actor("test_feature", User(1))
  assert client.actors("test_feature") == ["user:1"]
  assert client.is_enabled("test_feature", User(1))
  assert client.is_enabled("test_feature", "user:1")

def test_enable_actor_rejects_none():
  client = configured_client()
  client.add(build_feature())
  with pytest.raises(TypeError):
    client.enable_actor("test_feature", None)

@pytest.mark.parametrize("call", [
  lambda client: client.enable_actor("test_feature", "user:1"),
  lambda client: client.disable_actor("test_feature", "user:1"),
  lambda client: client.actors("test_feature"),
  lambda client: client.is_enabled("test_feature", "user:1"),
])
def test_actor_methods_raise_when_feature_not_found(call):
  client = configured_client()
  with pytest.raises(FeatureNotFound):
    call(client)
