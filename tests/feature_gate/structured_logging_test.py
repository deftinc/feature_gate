import io
import json
import pytest
import structlog

from feature_gate.adapters.memory import MemoryAdapter
from feature_gate.adapters.posthog import PosthogAdapter
from feature_gate.client import Client
from feature_gate.feature import Feature
from feature_gate.structured_logging import PROCESSORS, json_logger

@pytest.fixture(autouse=True)
def reset_structlog():
  yield
  structlog.reset_defaults()

def test_json_logger_writes_json_lines():
  out = io.StringIO()
  json_logger(out).info("hello", feature="my_flag")
  line = json.loads(out.getvalue())
  assert line["event"] == "hello"
  assert line["level"] == "info"
  assert line["feature"] == "my_flag"
  assert "timestamp" in line

def test_json_logger_defaults_to_stdout(capsys):
  json_logger().warning("to stdout")
  assert json.loads(capsys.readouterr().out)["event"] == "to stdout"

def test_json_logger_ignores_host_structlog_configuration():
  structlog.configure(
    processors=[structlog.dev.ConsoleRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(40),
  )
  out = io.StringIO()
  json_logger(out).info("still json")
  assert json.loads(out.getvalue())["event"] == "still json"

def test_adapters_use_the_logger_they_are_given():
  out = io.StringIO()
  client = Client(MemoryAdapter(logger=json_logger(out)))
  client.add(Feature("Name", "my_flag", "Description"))
  line = json.loads(out.getvalue())
  assert line["event"] == "add feature"
  assert line["klass"] == "MemoryAdapter"

def test_posthog_adapter_passes_its_logger_to_the_api_client():
  logger = json_logger(io.StringIO())
  adapter = PosthogAdapter(api_key="key", project_id="1", logger=logger)
  assert adapter.client.logger is logger
  assert adapter.logger is logger

def test_adapters_follow_host_structlog_configuration_by_default(capsys):
  processors = [structlog.dev.ConsoleRenderer(colors=False)]
  structlog.configure(processors=processors)
  adapter = MemoryAdapter()
  assert structlog.get_config()["processors"] is processors
  adapter.logger.info("host formatted")
  assert "host formatted" in capsys.readouterr().out

def test_processors_render_global_structlog_as_json(capsys):
  structlog.configure(processors=PROCESSORS)
  MemoryAdapter().logger.info("globally json")
  assert json.loads(capsys.readouterr().out)["event"] == "globally json"
