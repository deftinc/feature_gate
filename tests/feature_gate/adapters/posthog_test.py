import json
import pytest
import requests

from feature_gate.adapters.posthog import PosthogAdapter
from feature_gate.clients.posthog_api_client import RateLimitError
from feature_gate.client import Client, FeatureNotFound
from feature_gate.feature import Feature
from tests.fixtures.posthog_api_client.mocks import build_feature_from_mocks, mock_add_feature_funnel, mock_disable_feature_funnel, mock_enable_feature_funnel, mock_features_when_empty, mock_features_when_error_returned, mock_features_when_funnel, mock_funnel_is_disabled, mock_funnel_is_enabled, mock_remove_feature_funnel, mock_rate_limiting_error, mock_features_when_funnel_has_actors, mock_features_when_funnel_has_actors_and_catch_all, mock_features_when_funnel_is_enabled, mock_features_when_funnel_has_unmanaged_condition
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

def test_is_enabled_raises_an_error_when_rate_limited():
  client = configured_client()
  feature = build_feature_from_mocks()
  with patch.object(requests, 'get', return_value=mock_rate_limiting_error()):
    try:
      resp = client.is_enabled(feature.key)
    except RateLimitError as e:
      assert str(e) == "Request was throttled. Expected available in 5 seconds."

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

CATCH_ALL = {"properties": [], "rollout_percentage": None}
UNMANAGED = {
  "properties": [{"key": "email", "type": "person", "operator": "icontains", "value": "@example.com"}],
  "rollout_percentage": 50,
}

def actor_group(ids):
  return {
    "properties": [{"key": "distinct_id", "type": "person", "operator": "exact", "value": ids}],
    "rollout_percentage": 100,
  }

def sent_payload(network_mock):
  return json.loads(network_mock.call_args.kwargs["data"])

def test_is_enabled_for_an_enabled_actor():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_has_actors()):
    assert client.is_enabled("funnel_test", "user:1")
    assert client.is_enabled("funnel_test", "user:2", "user:1")
    assert not client.is_enabled("funnel_test", "user:2")
    assert not client.is_enabled("funnel_test")

def test_is_enabled_for_every_actor_when_globally_enabled():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_has_actors_and_catch_all()):
    assert client.is_enabled("funnel_test")
    assert client.is_enabled("funnel_test", "user:2")

def test_is_enabled_with_actors_is_false_when_flag_is_inactive():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    assert not client.is_enabled("funnel_test", "user:1")

def test_actors_lists_the_actor_group_values():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_has_actors()):
    assert client.actors("funnel_test") == ["user:1"]
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    assert client.actors("funnel_test") == []

def test_enable_actor_on_a_disabled_flag_replaces_the_catch_all():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    with patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()) as network_mock:
      assert client.enable_actor("funnel_test", "user:1")
      payload = sent_payload(network_mock)
  assert payload["active"] == True
  assert payload["filters"]["groups"] == [actor_group(["user:1"])]

def test_enable_actor_refuses_to_activate_unmanaged_conditions():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_has_unmanaged_condition()):
    with patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()) as network_mock:
      with pytest.raises(ValueError):
        client.enable_actor("funnel_test", "user:1")
      network_mock.assert_not_called()

def test_is_enabled_rejects_invalid_actors_without_an_actor_group():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    with pytest.raises(TypeError):
      client.is_enabled("funnel_test", 42)

def test_enable_actor_on_an_enabled_flag_keeps_the_catch_all():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_is_enabled()):
    with patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()) as network_mock:
      client.enable_actor("funnel_test", "user:1")
      payload = sent_payload(network_mock)
  assert payload["filters"]["groups"] == [CATCH_ALL, actor_group(["user:1"])]

def test_enable_actor_appends_to_the_actor_group_and_keeps_other_filters():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_has_actors()):
    with patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()) as network_mock:
      client.enable_actor("funnel_test", "user:2")
      payload = sent_payload(network_mock)
  assert payload["filters"]["groups"] == [UNMANAGED, actor_group(["user:1", "user:2"])]
  assert payload["filters"]["payloads"] == {}

def test_disable_actor_removes_the_actor():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_has_actors_and_catch_all()):
    with patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()) as network_mock:
      assert client.disable_actor("funnel_test", "user:1")
      payload = sent_payload(network_mock)
  assert payload["filters"]["groups"] == [CATCH_ALL]
  assert "active" not in payload

def test_disable_last_actor_on_a_disabled_flag_restores_the_catch_all_and_deactivates():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_has_actors()):
    with patch.object(requests, 'patch', return_value=mock_disable_feature_funnel()) as network_mock:
      assert client.disable_actor("funnel_test", "user:1")
      payload = sent_payload(network_mock)
  assert payload["active"] == False
  assert payload["filters"]["groups"] == [UNMANAGED, CATCH_ALL]

def test_disable_actor_is_a_noop_when_actor_is_not_enabled():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_has_actors()):
    with patch.object(requests, 'patch', return_value=mock_disable_feature_funnel()) as network_mock:
      assert client.disable_actor("funnel_test", "user:2")
      network_mock.assert_not_called()

def test_disable_with_actors_removes_the_catch_all_and_stays_active():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_has_actors_and_catch_all()):
    with patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()) as network_mock:
      assert client.disable("funnel_test")
      payload = sent_payload(network_mock)
  assert payload["active"] == True
  assert payload["filters"]["groups"] == [actor_group(["user:1"])]

def test_enable_with_actors_restores_the_catch_all():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel_has_actors()):
    with patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()) as network_mock:
      assert client.enable("funnel_test")
      payload = sent_payload(network_mock)
  assert payload["active"] == True
  assert payload["filters"]["groups"] == [UNMANAGED, actor_group(["user:1"]), CATCH_ALL]

def test_enable_and_disable_without_actors_only_toggle_active():
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_funnel()):
    with patch.object(requests, 'patch', return_value=mock_enable_feature_funnel()) as network_mock:
      client.enable("funnel_test")
      assert sent_payload(network_mock) == {"active": True}
    with patch.object(requests, 'patch', return_value=mock_disable_feature_funnel()) as network_mock:
      client.disable("funnel_test")
      assert sent_payload(network_mock) == {"active": False}

@pytest.mark.parametrize("call", [
  lambda client: client.enable_actor("funnel_test", "user:1"),
  lambda client: client.disable_actor("funnel_test", "user:1"),
  lambda client: client.actors("funnel_test"),
  lambda client: client.is_enabled("funnel_test", "user:1"),
])
def test_actor_methods_raise_when_feature_not_found(call):
  client = configured_client()
  with patch.object(requests, 'get', return_value=mock_features_when_empty()):
    with pytest.raises(FeatureNotFound):
      call(client)
