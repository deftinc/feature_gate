import pytest
import requests

from feature_gate.adapters.posthog import PosthogAdapter
from feature_gate.client import Client, FeatureNotFound
from feature_gate.feature import Feature
from tests.fixtures.posthog_api_client.mocks import build_feature_from_mocks, mock_add_feature_funnel, mock_disable_feature_funnel, mock_enable_feature_funnel, mock_features_when_empty, mock_features_when_error_returned, mock_features_when_funnel, mock_funnel_is_disabled, mock_funnel_is_enabled, mock_remove_feature_funnel
from unittest.mock import patch

def configured_client():
  adapter = PosthogAdapter(api_key="api_key", project_id="project_id")
  client = Client(adapter)
  return client

def build_feature():
  feature = Feature("Funnel Test", "funnel_test", "This is a feature flag tests a conversion funnel")
  return feature

def test_client_returns_api_client():
  client = configured_client()
  assert isinstance(client.adapter, PosthogAdapter)
  assert client.adapter.client.api_key == "api_key"
  assert client.adapter.client.project_id == "project_id"

def test_add_returns_true_when_feature_does_not_exist():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_features_when_empty()):
    with patch.object(requests, 'post', return_value=mock_add_feature_funnel()) as network_mock:
      resp = client.add(feature)
      assert resp == True
      network_mock.assert_called_once()

def test_add_returns_true_when_feature_does_exist():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    with patch.object(requests, 'post', return_value=mock_add_feature_funnel()) as network_mock:
      resp = client.add(feature)
      assert resp == True
      network_mock.assert_not_called()

def test_remove_returns_true_when_feature_does_exist():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    with patch.object(requests, 'patch', return_value=mock_remove_feature_funnel()) as network_mock:
      resp = client.remove(feature.key)
      assert resp == True
      network_mock.assert_called_once()

def test_remove_returns_true_when_feature_does_exist():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_features_when_empty()):
    with patch.object(requests, 'patch', return_value=mock_remove_feature_funnel()) as network_mock:
      resp = client.remove(feature.key)
      assert resp == True
      network_mock.assert_not_called()

def test_features_returns_list_of_features():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    resp = client.features()
    assert resp == ["funnel_test"]

def test_is_enabled_returns_true_when_feature_is_enabled():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_funnel_is_enabled()):
    resp = client.is_enabled(feature.key)
    assert resp == True

def test_is_enabled_returns_false_when_feature_is_disabled():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_funnel_is_disabled()):
    resp = client.is_enabled(feature.key)
    assert resp == False

def test_is_enabled_raises_an_error_when_the_feature_does_not_exist():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_features_when_empty()):
    try:
      resp = client.is_enabled(feature.key)
    except FeatureNotFound as e:
      assert str(e) == "Feature funnel_test not found"

def test_is_enabled_raises_an_error_when_the_api_response_returns_an_error_status():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_features_when_error_returned()):
    try:
      resp = client.is_enabled(feature.key)
    except FeatureNotFound as e:
      assert str(e) == "Feature funnel_test not found"

def test_enable_returns_true_when_feature_exists():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    with patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()) as network_mock:
      resp = client.enable(feature.key)
      assert resp == True
      network_mock.assert_called_once()

def test_enable_raises_error_when_feature_does_not_exist():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_features_when_empty()):
    with patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()) as network_mock:
      try:
        resp = client.enable(feature.key)
      except FeatureNotFound as e:
        assert str(e) == "Feature funnel_test not found"
      network_mock.assert_not_called()

def test_disable_returns_true_when_feature_exists():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    with patch.object(requests, 'patch', return_value=mock_disable_feature_funnel()) as network_mock:
      resp = client.disable(feature.key)
      assert resp == True
      network_mock.assert_called_once()

def test_disable_raises_error_when_feature_does_not_exist():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_features_when_empty()):
    with patch.object(requests, 'patch', return_value=mock_disable_feature_funnel()) as network_mock:
      try:
        resp = client.disable(feature.key)
      except FeatureNotFound as e:
        assert str(e) == "Feature funnel_test not found"
      network_mock.assert_not_called()
