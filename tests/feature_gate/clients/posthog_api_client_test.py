import pytest
import json
import os
from feature_gate.clients.posthog_api_client import PosthogAPIClient
from feature_gate.feature import Feature
from tests.fixtures.null_adapter import NullAdapter
from unittest.mock import Mock, patch
import requests


def build_feature_from_mocks():
  feature = Feature("Funnel Test", "funnel_test", "This is a feature flag tests a conversion funnel")
  return feature

def load_response(fixture_name):
  file_path = f'./tests/fixtures/posthog_api_client/{fixture_name}.json'
  try:
    with open(file_path, 'r') as json_file:
      return json.load(json_file)
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
  return PosthogAPIClient(api_key="api_key", project_id="project_id")

def test_api_returns_api_key_instantiated():
  client = configured_client()
  assert client.api_key == "api_key"

def test_project_id_returns_project_id_instantiated():
  client = configured_client()
  assert client.project_id == "project_id"

def test_api_base_uses_default():
  client = configured_client()
  assert client.api_base == "https://app.posthog.com"

def test_list_features_returns_a_list_of_features():
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    client = configured_client()
    response = client.list_features()
    assert "data" in response and "pagination" in response
    assert len(response["data"]) == 1
    assert response["data"][0]["key"] == "funnel_test"
    assert response["data"][0]["name"] == "This is a feature flag tests a conversion funnel"

def test_create_feature_returns_the_feature_created():
  with patch.object(requests, 'post', return_value=mock_add_feature_funnel()):
    client = configured_client()
    feature = build_feature_from_mocks()
    response = client.create_feature(feature.key, feature.description)
    assert response["data"]["key"] == "funnel_test"
    assert response["data"]["name"] == "This is a feature flag tests a conversion funnel"
    assert response["data"]["deleted"] == False

def test_fetch_feature_returns_the_feature():
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    client = configured_client()
    feature = build_feature_from_mocks()
    response = client.fetch_feature(feature.key)
    assert response["key"] == "funnel_test"
    assert response["name"] == "This is a feature flag tests a conversion funnel"
    assert response["deleted"] == False

def test_fetch_feature_returns_none_when_not_found():
  with patch.object(requests, 'get', return_value=mock_features_when_empty()):
    client = configured_client()
    response = client.fetch_feature("not_found")
    assert response == None

def test_delete_feature_returns_the_feature_deleted():
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()), patch.object(requests, 'patch', return_value=mock_remove_feature_funnel()):
    client = configured_client()
    feature = build_feature_from_mocks()
    response = client.delete_feature(feature.key)
    assert response["data"]["key"] == "funnel_test"
    assert response["data"]["name"] == "This is a feature flag tests a conversion funnel"
    assert response["data"]["deleted"] == True

def test_is_enabled_returns_true_when_enabled():
  with patch.object(requests, 'get', return_value=mock_funnel_is_enabled()):
    client = configured_client()
    feature = build_feature_from_mocks()
    response = client.is_enabled(feature.key)
    assert response == True

def test_is_enabled_returns_false_when_disabled():
  with patch.object(requests, 'get', return_value=mock_funnel_is_disabled()):
    client = configured_client()
    feature = build_feature_from_mocks()
    response = client.is_enabled(feature.key)
    assert response == False

def test_enable_feature_returns_the_feature_enabled():
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()), patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()):
    client = configured_client()
    feature = build_feature_from_mocks()
    response = client.enable_feature(feature.key)
    assert response["data"]["key"] == "funnel_test"
    assert response["data"]["name"] == "This is a feature flag tests a conversion funnel"
    assert response["data"]["active"] == True

def test_disable_feature_returns_the_feature_disabled():
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()), patch.object(requests, 'patch', return_value=mock_disable_feature_funnel()):
    client = configured_client()
    feature = build_feature_from_mocks()
    response = client.disable_feature(feature.key)
    assert response["data"]["key"] == "funnel_test"
    assert response["data"]["name"] == "This is a feature flag tests a conversion funnel"
    assert response["data"]["active"] == False

def test_enable_feature_raises_exception_when_not_found():
  with patch.object(requests, 'get', return_value=mock_features_when_empty()):
    client = configured_client()
    feature = build_feature_from_mocks()
    with pytest.raises(Exception) as e:
      client.enable_feature(feature.key)
    assert str(e.value) == f"Feature {feature.key} not found"

def test_disable_feature_raises_exception_when_not_found():
  with patch.object(requests, 'get', return_value=mock_features_when_empty()):
    client = configured_client()
    feature = build_feature_from_mocks()
    with pytest.raises(Exception) as e:
      client.disable_feature(feature.key)
    assert str(e.value) == f"Feature {feature.key} not found"

def test_is_enabled_raises_exception_when_not_found():
  with patch.object(requests, 'get', return_value=mock_features_when_empty()):
    client = configured_client()
    feature = build_feature_from_mocks()
    with pytest.raises(Exception) as e:
      client.is_enabled(feature.key)
    assert str(e.value) == f"Feature {feature.key} not found"

def test_log_error_on_posthog_connection():
  with patch.object(requests, 'get', side_effect=requests.ConnectionError('Mocked error')):
    with patch.object(PosthogAPIClient, '_log_posthog_connection_error') as mock_log:
      mock_log.assert_called_once
