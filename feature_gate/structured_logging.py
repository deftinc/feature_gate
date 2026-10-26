import logging
import sys
import structlog

from structlog.contextvars import merge_contextvars

# Pass to structlog.configure(processors=PROCESSORS) to render every structlog
# logger in the process, feature_gate's included, as JSON.
PROCESSORS = [
  merge_contextvars,
  structlog.processors.add_log_level,
  structlog.processors.TimeStamper(fmt="iso"),
  structlog.processors.dict_tracebacks,
  structlog.processors.JSONRenderer(),
]

def json_logger(file=None):
  """Returns a logger that writes one JSON object per line to `file` (stdout by default).

  Pass it as an adapter's `logger=` to get JSON logs from feature_gate alone.
  It carries its own processors and wrapper class, so the host application's
  structlog configuration doesn't affect it.
  """
  return structlog.wrap_logger(
    structlog.WriteLogger(file or sys.stdout),
    processors=PROCESSORS,
    wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
  )
