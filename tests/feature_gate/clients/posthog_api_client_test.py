import pytest
import json
import os
from feature_gate.clients.posthog_api_client import PosthogAPIClient
from tests.fixtures.null_adapter import NullAdapter
from unittest.mock import Mock, patch
import requests

feature = Feature("Funnel Test", "funnel_test", "This is a feature flag tests a conversion funnel")

def load_response(fixture_name):
  file_path = f'./tests/fixtures/posthog_api_client/{fixture_name}.json'
  try:
    with open(file_path, 'r') as file:
      return json.read(file)
  except FileNotFoundError:
    raise Exception(f"Fixture not found. \n{file_path}")
  except json.JSONDecodeError:
    raise Exception(f"Fixture is not valid JSON. \n{file_path}")
  except IOError:
    raise Exception(f"Could not open fixture. \n{file_path}")

def mock_features_when_empty():
  return Mock(
    status_code=200,
    json=Mock(
      return_value=load_response('get_features_when_empty')
    )
  )

def mock_features_when_funnel():
  return Mock(
    status_code=200,
    json=Mock(
      return_value=load_response('get_features_when_funnel')
    )
  )

def mock_add_feature_funnel():
  return Mock(
    status_code=200,
    json=Mock(
      return_value=load_response('add_feature_funnel')
    )
  )

def mock_remove_feature_funnel():
  return Mock(
    status_code=200,
    json=Mock(
      return_value=load_response('remove_feature_funnel')
    )
  )

def mock_enable_feature_funnel():
  return Mock(
    status_code=200,
    json=Mock(
      return_value=load_response('enable_feature_funnel')
    )
  )

def mock_disable_feature_funnel():
  return Mock(
    status_code=200,
    json=Mock(
      return_value=load_response('disable_feature_funnel')
    )
  )

def mock_funnel_is_enabled():
  return Mock(
    status_code=200,
    json=Mock(
      return_value=load_response('funnel_is_enabled')
    )
  )

def mock_funnel_is_disabled():
  return Mock(
    status_code=200,
    json=Mock(
      return_value=load_response('funnel_is_disabled')
    )
  )

def configured_client():
  return PosthogAPIClient("api_key", "project_id")

def test_api_returns_api_key_instantiated():
  client = configured_client()
  assert client.adapter.api_key == "api_key"

def test_project_id_returns_project_id_instantiated():
  client = configured_client()
  assert client.adapter.api_key == "api_key"

def test_list_features_returns_a_list_of_features():
  with patch.object(requests, 'post', return_value=list_mock_return()):
    client = configured_client()
    client.adapter.list_features() == ["feature_1", "feature_2"]
