import os
import importlib
import feature_gate.client
import feature_gate.clients
import feature_gate.clients.posthog
import feature_gate.feature
import feature_gate.adapters
import feature_gate.adapters.mongo
import feature_gate.adapters.posthog

from pymongo import MongoClient
from feature_gate.adapters.mongo import MongoAdapter
from feature_gate.adapters.posthog import PosthogAdapter
from feature_gate.client import Client
from feature_gate.clients.posthog import PosthogAPI
from feature_gate.feature import Feature

def posthog_client() -> Client:
  posthog_api_key = os.environ.get('POSTHOG_API_KEY')
  posthog_project_id = os.environ.get('POSTHOG_PROJECT_ID')
  adapter = PosthogAdapter(posthog_api_key, posthog_project_id)
  return Client(adapter)

def mongo_client() -> Client:
  db = MongoClient('mongodb://feature_gate:feature_gate@localhost:27017/feature_gate')
  adapter = MongoAdapter(db)
  return Client(adapter)
