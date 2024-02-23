import os
import importlib
import feature_gate.client
import feature_gate.clients
import feature_gate.clients.posthog_api_client
import feature_gate.feature
import feature_gate.adapters
import feature_gate.adapters.posthog

from feature_gate.adapters.posthog import PosthogAdapter
from feature_gate.client import Client
from feature_gate.clients.posthog_api_client import PosthogAPIClient
from feature_gate.feature import Feature

def posthog_client() -> Client:
  adapter = PosthogAdapter()
  return Client(adapter)

