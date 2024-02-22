import json
from feature_gate.feature import Feature
from unittest.mock import Mock

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
