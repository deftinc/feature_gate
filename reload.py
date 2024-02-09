importlib.reload(importlib)
importlib.reload(feature_gate.client)
importlib.reload(feature_gate.feature)
importlib.reload(feature_gate.adapters)
importlib.reload(feature_gate.adapters.mongo)

from pymongo import MongoClient
from feature_gate.adapters.mongo import MongoAdapter
from feature_gate.client import Client
