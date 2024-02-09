import importlib
import feature_gate.client
import feature_gate.feature
import feature_gate.adapters
import feature_gate.adapters.mongo

from pymongo import MongoClient
from feature_gate.adapters.mongo import MongoAdapter
from feature_gate.client import Client

def client() -> Client:
  db = MongoClient('mongodb://feature_gate:feature_gate@localhost:27017/feature_gate')
  adapter = MongoAdapter(db)
  return Client(adapter)
