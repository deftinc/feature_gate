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
