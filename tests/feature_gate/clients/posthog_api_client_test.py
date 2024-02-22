import pytest
import requests

from feature_gate.clients.posthog_api_client import PosthogAPIClient, PosthogAPIClientError
from tests.fixtures.posthog_api_client.mocks import build_feature_from_mocks, load_response, mock_add_feature_funnel, mock_disable_feature_funnel, mock_enable_feature_funnel, mock_features_when_empty, mock_features_when_funnel, mock_funnel_is_disabled, mock_funnel_is_enabled, mock_remove_feature_funnel
from unittest.mock import patch

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

def test_raise_posthog_api_client_error_on_conncetion_errors():
  with patch.object(requests, 'get', side_effect=requests.ConnectionError('Mocked error')):
    try:
      client = configured_client()
      client.list_features()
    except PosthogAPIClientError as e:
      assert str(e) == "Posthog connection error - Mocked error"

def test_log_errors_on_posthog_connection():
  client = configured_client()
  with patch.object(requests, 'get', side_effect=requests.ConnectionError('Mocked error')):
    with patch.object(client.logger, 'error', side_effect=PosthogAPIClientError()) as mock_log:
      try:
        client.list_features()
      except PosthogAPIClientError as e:
        mock_log.assert_called_once()
