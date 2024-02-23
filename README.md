# FeatureGate

Featuregate is a simple feature flag API similar to [Flipper](https://github.com/flippercloud/flipper).

## Configuration

### PosthogAdapter

```bash
export POSTHOG_API_KEY="someapikey"
export POSTHOG_PROJECT_ID="someprojectid"
```

## Usage

```python
from feature_gate.client import Client
from feature_gate.adapters import PosthogAdapter
from feature_gate.feature import Feature

adapter = PosthogAdapter() # Or MemoryAdapter for testing
client = Client(adapter)
feature = Feature("Test flag", "test_flag", "This is a test flag")

client.features()
# => []

client.add(feature)
# => True

client.features()
# => ["test_flag"]

client.is_enabled("test_flag")
# => False

client.enable("test_flag")
# => True

client.is_enabled("test_flag")
# => True

client.disable("test_flag")
# => True

client.is_enabled("test_flag")
# => False

client.remove("test_flag")
# => True

client.features()
# => []
```

## Errors

### FeatureNotFound
If you try to run something that presumes the existence of a feature and it can't find it it'll throw a `FeatureNotFound`.

```python
from feature_gate.client import FeatureNotFound

try:
  client.remove("some_feature_that_definitely_does_not_exist")
except FeatureNotFound as err:
  # Do what we want to do when the feature doesn't exist
```

### PostApiClientError
For the `PosthogAdapter` in particular it will raise error if it was unable to reach the Posthog API. These get bubbled up as `PosthogAPIClientError`.

```python
from feature_gate.clients.posthog_api_client import PosthogAPIClientError

try:
  client.features() #disable network connection
except PosthogAPIClientError as err:
  # Handle the error -- define default behavior in outage
```

## Testing

The Memory Adapter can be used for writing tests. This creates an ephemeral memory only implementation of the feature_gate client API. This is non-suitable for production only for tests.

```python
from feature_gate.client import Client
from feature_gate.adapters.memory import MemoryAdapter

client = Client(MemoryAdapter())
```

## Developing this library

### Hot-reload the REPL

Hot-reload the client in the repl for development:

```
$ repl
>>> exec(open('reload.py').read())
```
