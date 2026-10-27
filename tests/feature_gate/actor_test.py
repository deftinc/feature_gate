import pytest
from feature_gate.actor import actor_id

class User:
  def __init__(self, id):
    self.feature_gate_id = f"user:{id}"

def test_string_is_its_own_id():
  assert actor_id("user:42") == "user:42"

def test_object_uses_its_feature_gate_id():
  assert actor_id(User(42)) == "user:42"

def test_feature_gate_id_is_converted_to_a_string():
  actor = type("Actor", (), {"feature_gate_id": 7})()
  assert actor_id(actor) == "7"

@pytest.mark.parametrize("actor", [42, None, object()])
def test_rejects_actors_without_an_id(actor):
  with pytest.raises(TypeError):
    actor_id(actor)

@pytest.mark.parametrize("actor", ["", type("Actor", (), {"feature_gate_id": ""})()])
def test_rejects_empty_ids(actor):
  with pytest.raises(ValueError):
    actor_id(actor)
