import pytest
from feature_gate.feature import Feature

def feature_fixture():
  name = "Phone Sales"
  key = "phone_sales"
  description = "Enable phone sales funnel optimization"
  return Feature(name, key, description)

def test_name_returns_name_as_instantiated():
  feature = feature_fixture()
  assert feature.name == "Phone Sales"

def test_key_returns_key_as_instantiated():
  feature = feature_fixture()
  assert feature.key == "phone_sales"

def test_description_returns_description_as_instantiated():
  feature = feature_fixture()
  assert feature.description == "Enable phone sales funnel optimization"
