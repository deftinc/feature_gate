import json
import requests
import structlog
from pathlib import Path

from structlog.contextvars import (
    bind_contextvars,
    merge_contextvars,
    bound_contextvars,
)

class PosthogAPI:
  def __init__(self, api_key, project_id):
    self.api_key = api_key
    self.host='https://app.posthog.com'
    self.project_id = project_id

    bind_contextvars(klass="PosthogAPI", project_id=project_id)
    structlog.configure(
      processors=[
        merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
      ],
      logger_factory=structlog.WriteLoggerFactory(
        file=Path("development").with_suffix(".log").open("wt")
      ),
    )
    self.logger = structlog.get_logger()

  def api_key(self):
     return self.api_key

  def project_id(self):
    return self.project_id

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
    features = self.list_features()["data"]
    for entry in features:
        if "key" in entry and entry["key"] == key:
            return entry
    return None

  def delete_feature(self, key):
    feature = self.fetch_feature(key)
    if feature == None:
      raise Exception(f"Feature {key} not found")
    else:
      path = f'/api/projects/{self.project_id}/feature_flags/{feature["id"]}'
      with bound_contextvars(method="delete_feature"):
        payload = {
          'deleted': True
        }
        response = self._patch(path, payload)
        return self._map_single_response("PATCH", path, response)

  def is_enabled(self, key):
    feature = self.fetch_feature(key)
    if feature == None:
      raise Exception(f"Feature {key} not found")
    else:
      return feature["active"]

  def enable_feature(self, key):
    feature = self.fetch_feature(key)
    if feature == None:
      raise Exception(f"Feature {key} not found")
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
      raise Exception(f"Feature {key} not found")
    else:
      path = f'/api/projects/{self.project_id}/feature_flags/{feature["id"]}'
      with bound_contextvars(method="disable_feature"):
        payload = {
          'active': False
        }
        response = self._patch(path, payload)
        return self._map_single_response("PATCH", path, response)

  def _get(self, path):
    with bound_contextvars(method="get"):
      url = f"{self.host}{path}"
      headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.api_key}"
      }
      response = requests.get(url, headers=headers)
      print(f"GET {url}\n{response}")
      return response

  def _post(self, path, payload):
    url = f"{self.host}{path}"
    with bound_contextvars(method="post", url=url):
      json_payload = json.dumps(payload)
      headers = self._get_headers()
      response = requests.post(url, data=json_payload, headers=headers)
      print(f"POST {url}\n{response}")
      return response

  def _patch(self, path, payload):
    url = f"{self.host}{path}"
    with bound_contextvars(method="patch", url=url):
      json_payload = json.dumps(payload)
      headers = self._get_headers()
      response = requests.patch(url, data=json_payload, headers=headers)
      print(f"PATCH {url}\n{response}")
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
