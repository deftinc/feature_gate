import pytest
from feature_gate.client import Client
from tests.fixtures.null_adapter import NullAdapter
from unittest.mock import Mock, patch

def test_adapter_returns_the_configured_adapter():
  adapter = NullAdapter()
  client = Client(adapter)
  assert client.adapter == adapter

def test_delegates_add_to_the_adapter():
  with patch.object(NullAdapter, 'add', return_value=None) as mock_add:
    adapter = NullAdapter()
    client = Client(adapter)
    client.add('feature')
    mock_add.assert_called_once_with('feature')

def test_delegates_remove_to_the_adapter():
  with patch.object(NullAdapter, 'remove', return_value=None) as mock_remove:
    adapter = NullAdapter()
    client = Client(adapter)
    client.remove('feature')
    mock_remove.assert_called_once_with('feature')

def test_delegates_features_to_the_adapter():
  with patch.object(NullAdapter, 'features', return_value=None) as mock_features:
    adapter = NullAdapter()
    client = Client(adapter)
    client.features()
    mock_features.assert_called_once()

def test_delegates_is_enabled_to_the_adapter():
  with patch.object(NullAdapter, 'is_enabled', return_value=None) as mock_is_enabled:
    adapter = NullAdapter()
    client = Client(adapter)
    client.is_enabled('feature')
    mock_is_enabled.assert_called_once_with('feature')

def test_delegates_enable_to_the_adapter():
  with patch.object(NullAdapter, 'enable', return_value=None) as mock_enable:
    adapter = NullAdapter()
    client = Client(adapter)
    client.enable('feature')
    mock_enable.assert_called_once_with('feature')

def test_delegates_disable_to_the_adapter():
  with patch.object(NullAdapter, 'disable', return_value=None) as mock_disable:
    adapter = NullAdapter()
    client = Client(adapter)
    client.disable('feature')
    mock_disable.assert_called_once_with('feature')
