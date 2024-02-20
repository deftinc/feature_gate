import pytest
from feature_gate.feature import Feature
from feature_gate.client import Client
from feature_gate.adapters.posthog import PosthogAdapter
from tests.fixtures.null_adapter import NullAdapter

def configured_client():
  adapter = PosthogAdapter("api_key", "project_id")
  client = Client(adapter)
  return client

def test_client_returns_api_client():
  client = configured_client()
  client.client.api_key == "api_key"
  client.client.project_id == "project_id"


def test_add_returns_true():
  with patch.object(PosthogAdapter, 'add', return_value=None) as mock_add:

def test_add_creates_a_feature():


def test_remove_returns_null():
def test_remove_deletes_a_feature():

def test_features_returns_a_list_of_feature_keys():
def test_is_enabled_returns_true_if_feature_is_enabled():
def test_is_enabled_returns_false_if_feature_is_disabled():
def test_is_enabled_raises_an_error_if_feature_is_missing():

