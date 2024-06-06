import json
import os
import requests
import structlog
from posthog import Posthog

from pathlib import Path
from feature_gate.client import FeatureNotFound

from structlog.contextvars import (
    bind_contextvars,
    merge_contextvars,
    bound_contextvars,
)

class PosthogAPIClientError(Exception):
  pass

class PosthogAPIClient:
  def __init__(self, api_base=None, api_key=None, project_id=None, poll_interval=30):
    if api_base is None:
      self.api_base = os.environ.get("POSTHOG_API_BASE", "https://app.posthog.com")
    else:
      self.api_base = api_base

    if api_key is None:
      self.api_key = os.environ.get('POSTHOG_API_KEY')
    else:
      self.api_key = api_key

    if project_id is None:
      self.project_id = os.environ.get('POSTHOG_PROJECT_ID')
    else:
      self.project_id = project_id
    
    self.posthog_client = Posthog(project_id,
                             host=self.api_base,
                             poll_interval=poll_interval, # local eval refresh interval
                             personal_api_key=api_key
    )

    bind_contextvars(klass="PosthogAPIClient", project_id=project_id)
    project_root = os.path.abspath(os.getenv('PROJECT_ROOT', '.'))
    logs_dir_path = Path(project_root, 'logs')
    logs_dir_path.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir_path.joinpath('development').with_suffix('.log').open('at')
    structlog.configure(
      processors=[
        merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
      ],
      logger_factory=structlog.WriteLoggerFactory(file=log_file),
    )
    self.logger = structlog.get_logger()

  def api_base(self):
    return self.api_base

  def api_key(self):
     return self.api_key

  def project_id(self):
    return self.project_id


  def is_enabled(self, key, user_id=None, person_properties=None, only_evaluate_locally=False, **kwargs):
    """
    This uses posthog local evaluation to check if a feature flag is enabled 
    for a user without making a server request.
    See local eval docs here: https://posthog.com/docs/feature-flags/local-evaluation

    Args:
        name (String): the name/key of the feature flag
        user (User): the user object

    Returns:
        bool: true or false
    """
    return self.posthog_client.get_feature_flag(
      key,
      user_id,
      # Include any person properties, groups, or group properties required to evaluate the flag
      person_properties=person_properties,
      # Optional. Defaults to False. Set to True if you don't want PostHog to make a server request if it can't evaluate locally
      only_evaluate_locally=only_evaluate_locally,
      **kwargs
    )


  def list_features(self):
    path = f'/api/projects/{self.project_id}/feature_flags'
    with bound_contextvars(method="list_features"):
      response = self._get(path)
      return self._map_list_response("GET", path, response)

  def create_feature(self, name, description, deleted=False, active=False):
    with bound_contextvars(method="create_feature"):
      path = f'/api/projects/{self.project_id}/feature_flags'
      payload = {
        'name': description,
        'key': name,
        'deleted': deleted,
        'active': active
      }
      response = self._post(path, payload)
      return self._map_single_response("POST", path, response)

  def fetch_feature(self, key):
    features = self.list_features().get("data", [])
    for entry in features:
        if "key" in entry and entry["key"] == key:
            return entry
    return None

  def delete_feature(self, key):
    feature = self.fetch_feature(key)
    if feature == None:
      raise FeatureNotFound(f"Feature {key} not found")
    else:
      path = f'/api/projects/{self.project_id}/feature_flags/{feature["id"]}'
      with bound_contextvars(method="delete_feature"):
        payload = {
          'deleted': True
        }
        response = self._patch(path, payload)
        return self._map_single_response("PATCH", path, response)

  def enable_feature(self, key):
    feature = self.fetch_feature(key)
    if feature == None:
      raise FeatureNotFound(f"Feature {key} not found")
    else:
      path = f'/api/projects/{self.project_id}/feature_flags/{feature["id"]}'
      with bound_contextvars(method="enable_feature"):
        payload = {
          'active': True
        }
        response = self._patch(path, payload)
        return self._map_single_response("PATCH", path, response)

  def disable_feature(self, key):
    feature = self.fetch_feature(key)
    if feature == None:
      raise FeatureNotFound(f"Feature {key} not found")
    else:
      path = f'/api/projects/{self.project_id}/feature_flags/{feature["id"]}'
      with bound_contextvars(method="disable_feature"):
        payload = {
          'active': False
        }
        response = self._patch(path, payload)
        return self._map_single_response("PATCH", path, response)

  def _get(self, path):
    try:
      return self.__get(path)
    except requests.ConnectionError as err:
      self._log_posthog_connection_error(err)

  def __get(self, path):
    with bound_contextvars(method="get"):
      url = f"{self.api_base}{path}"
      headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.api_key}"
      }
      response = requests.get(url, headers=headers)
      return response

  def _post(self, path, payload):
    try:
      return self.__post(path, payload)
    except requests.ConnectionError as err:
      self._log_posthog_connection_error(err)

  def __post(self, path, payload):
    url = f"{self.api_base}{path}"
    with bound_contextvars(method="post", url=url):
      json_payload = json.dumps(payload)
      headers = self._get_headers()
      response = requests.post(url, data=json_payload, headers=headers)
      return response

  def _patch(self, path, payload):
    try:
      return self.__patch(path, payload)
    except requests.ConnectionError as err:
      self._log_posthog_connection_error(err)

  def __patch(self, path, payload):
    url = f"{self.api_base}{path}"
    with bound_contextvars(method="patch", url=url):
      json_payload = json.dumps(payload)
      headers = self._get_headers()
      response = requests.patch(url, data=json_payload, headers=headers)
      return response

  def _get_headers(self):
    return {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {self.api_key}"
    }

  def _check_status_ok(self, code):
    return code == 200 or code == 201

  def _map_single_response(self, method, path, response):
    ret = None
    if self._check_status_ok(response.status_code):
        data = response.json()
        self.logger.info("request successful", method=method, path=path, status_code=response.status_code, response=data)
        ret = self._map_single_response_success(data)
    else:
        data = response.json()
        self.logger.info("request failed", method=method, path=path, status_code=response.status_code, response=data)
        ret = self._map_error_response(response.status_code, data)
    return ret

  def _map_list_response(self, method, path, response):
    ret = None
    if self._check_status_ok(response.status_code):
        data = response.json()
        self.logger.info("request successful", method=method, path=path, status_code=response.status_code, response=data)
        ret = self._map_list_response_success(data)
    else:
        data = response.json()
        self.logger.info("request failed", method=method, path=path, status_code=response.status_code, response=data)
        ret = self._map_error_response(response.status_code, data)
    return ret

  def _map_error_response(self, code, data):
    return {
      "errors": [
        {
          "status": code,
          "detail": data.get("detail"),
          "code": data.get("code"),
          "type": data.get("type")
        }
      ]
    }

  def _map_single_response_success(self, data):
    return {
      "data": data
    }

  def _map_list_response_success(self, data):
    return {
      "data": data.get("results"),
      "pagination": {
        "next": data.get("next"),
        "previous": data.get("previous")
      }
    }

  def _log_posthog_connection_error(self, error):
    self.logger.error(f"Posthog connection error - {error}")
    raise PosthogAPIClientError(f"Posthog connection error - {error}")
