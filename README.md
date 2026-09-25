# BYOConfig

> Bring your own configuration

A configuration class supporting multiple file formats, environment variables, AWS Secrets Manager, singletons, and more.

## Features

- Loading/Dumping configuration data using:
  - YAML
  - TOML
  - JSON
  - Environment Variables
- Loading secrets from AWS Secrets Manager
- File type detection
- Filtering configuration data by key name prefix
- Filtering configuration data by a `typing.Annotated` type
- Excluding configuration data from file dumps

## Installing

Requires Python 3.10 or newer.

```bash
pip install byoconfig
```

## Usage

### Declaring Your Configuration

Configuration keys are declared as class attributes on a subclass of `BYOConfig`. Each key must be assigned a default value.

```python
from byoconfig import BYOConfig


class AppConfig(BYOConfig):
    host: str = "localhost"
    port: int = 8080


config = AppConfig()

print(config.get("host"))
# > localhost

config.set("port", 9000)
config.update({"host": "example.com"})
print(config.as_dict())
# > {'host': 'example.com', 'port': 9000}
```

Only the keys declared in your subclass's body are configuration data. Attributes inherited from parent classes, names starting with an underscore, methods, and properties are ignored.

`set` and `update` only accept declared keys, and raise a `KeyError` for anything else. Attributes assigned directly to an instance are also treated as configuration data.

```python
config.debug = True
print(config.get("debug"))
# > True

config.set("missing", 1)
# > KeyError: 'No attr with name missing'
```

`delete_item` removes a value set on the instance, reverting a declared key to its class default. `clear_data` does the same for every key, or only the keys given to it.

```python
config.delete_item("port")
print(config.get("port"))
# > 8080

config.clear_data()
print(config.as_dict())
# > {'host': 'localhost', 'port': 8080}
```

A config instance also supports `keys()`, `values()`, `items()`, `len()`, `in`, and iteration over its key names.

### From File

```python
from byoconfig import BYOConfig

"""
# path/to/config.yaml
host: example.com
port: 443
"""


class AppConfig(BYOConfig):
    host: str = "localhost"
    port: int = 8080


config = AppConfig()

# Detects the file type from the file extension (.json, .yaml, .yml, or .toml)
config.load_from_file("path/to/config.yaml")

# Alternatively, force the file type (One of 'JSON', 'YAML', or 'TOML')
config.load_from_file("path/to/config", forced_type="YAML")
```

Every top-level key in the file must be declared in your subclass, otherwise a `KeyError` is raised.

Other options for `load_from_file`:

- `not_exists_ok=True` skips loading, instead of raising `FileNotFoundError`, when the file does not exist or the path is `None`.
- `enforce_mapping_type=True` raises a `TypeError` if the top level of the file is not a mapping.

Files that can't be decoded raise a `ValueError`, with the original decoding error as its `__cause__`. An empty file loads nothing.

To read a file's contents without applying them, use `get_data_from_file`, which accepts the same arguments and returns the data.

### From Environment Variables

Variable names are lowercased when loaded, and the prefix (plus a trailing underscore) is trimmed from the name by default.

```python
from os import environ

from byoconfig import BYOConfig


class AppConfig(BYOConfig):
    var_1: str = ""
    something_something: str = ""
    home: str = ""


# Environment variables are always stored as strings
environ.update({"MY_APP_VAR_1": "1", "TEST_SOMETHING_SOMETHING": "2"})

config = AppConfig()
config.load_from_environment(prefix="MY_APP")
print(config.get("var_1"))
# > 1

# Loading again with a different prefix
config.load_from_environment(prefix="TEST")
print(config.get("something_something"))
# > 2

# Keep the prefix in the key names
config.load_from_environment(prefix="MY_APP", trim_prefix=False)

# Use '*' as the prefix to load from every environment variable
config.load_from_environment(prefix="*")
print(config.get("home"))
# > /home/user
```

Environment variables that don't match a declared key are skipped.

The prefix must be a valid environment variable name, matching `^[a-zA-Z_][a-zA-Z0-9_]*$`. On Windows, the prefix is uppercased before matching.

### To Environment Variables

```python
from os import environ

from byoconfig import BYOConfig


class AppConfig(BYOConfig):
    host: str = "localhost"
    port: int = 8080


config = AppConfig()

# Sets HOST and PORT. Values are converted to strings.
config.dump_to_environment()

# Sets MY_APP_HOST and MY_APP_PORT
config.dump_to_environment(with_prefix="my_app")

# Sets my_app_host only
config.dump_to_environment(selected_keys=["host"], use_uppercase=False, with_prefix="my_app")

print(environ["MY_APP_PORT"])
# > 8080
```

Selecting a key that isn't defined raises a `KeyError`, and an invalid prefix or variable name raises a `ValueError`.

### From AWS Secrets Manager

Secrets must be stored as JSON. Credentials are resolved by `boto3` in the usual way, see the
[boto3 credentials guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html).

```python
from byoconfig import BYOConfig

# AWS Secrets Manager secrets, using the JSON option.
# Keys from each secret are merged into the config, so later secrets overwrite matching keys.
"""
# Where the name of the secret is api_keys/important
{
    "important_api_key": "B3U1+L/ZLKfFfdLf+cdx/7f9HhMjiL6meZlS11RlojQ"
}

# Where the name of the secret is api_keys/different
{
    "different_api_key": "Jc6Qq37sV+3SidDmkQ42RXtq1x7qEAQUZKCVr7JzADM"
}
"""


class APIConfig(BYOConfig):
    important_api_key: str = ""
    different_api_key: str = ""


class ImportantAPIClient:
    def __init__(self, config: APIConfig):
        self.api_key = config.get("important_api_key")


class DifferentAPIClient:
    def __init__(self, config: APIConfig):
        self.api_key = config.get("different_api_key")


def main():
    config = APIConfig()
    config.load_from_secrets_manager("api_keys/important")
    important_api_client = ImportantAPIClient(config)

    # Additional keyword arguments are passed to boto3.client
    config.load_from_secrets_manager("api_keys/different", region_name="us-west-2")
    different_api_client = DifferentAPIClient(config)
```

As with files, every top-level key in the secret must be declared in your subclass. A secret that isn't valid JSON raises a `ValueError`.

### Dumping Data

An example of dumping the contents of your config to a file.

```python
from byoconfig import BYOConfig


class AppConfig(BYOConfig):
    host: str = "localhost"
    port: int = 8080


config = AppConfig()

# Detects the file type from the file extension
config.dump_to_file("running_config.yml")

# Force the file type when the file has no extension
config.dump_to_file("running_config", forced_type="TOML")
```

Missing parent directories are created. If a value can't be serialized to the chosen format, a `TypeError` is raised and no file or directory is created. YAML is written with `yaml.safe_dump`, so tuples are written as lists, and values such as sets or arbitrary objects are rejected.

An example of excluding configuration data from the `dump_to_file` method output.

```python
from typing import Annotated

from byoconfig import BYOConfig


class MyConfig(BYOConfig):
    not_critically_secret_data: str = "This can be exported to file"
    super_secret_data: Annotated[str, "excluded"] = ""


config = MyConfig()
config.set("super_secret_data", "an API key or something you don't want to share")

# The resulting file will not contain 'super_secret_data' or any other key annotated with "excluded"
config.dump_to_file("my_config.json")

# The data that would be dumped
print(config.exportable_data)
# > {'not_critically_secret_data': 'This can be exported to file'}
```

### Filtering Data

#### By Key Name Prefix

We can group our configuration data by the kwargs for a function/method/class, prefixing each parameter with a name.

Using `uvicorn` as the prefix to supply kwargs to `uvicorn.run`:

```python
import uvicorn

from byoconfig import BYOConfig

# like fastapi or starlette
from my_app.asgi import asgi_app


class AppConfig(BYOConfig):
    uvicorn_port = 8889
    uvicorn_host = "127.0.0.1"
    uvicorn_log_level = "info"


def run_server():
    config = AppConfig()

    # Results in the dict: {'port': 8889, 'host': '127.0.0.1', 'log_level': 'info'}
    uvicorn_kwargs = config.get_by_prefix("uvicorn")

    uvicorn.run(asgi_app, **uvicorn_kwargs)
```

Pass `trim_prefix=False` to keep the prefix in the returned key names.

#### By Annotated Type

We can group our configuration data in arbitrary categories by supplying metadata via `typing.Annotated`.

Same example as before, but with annotations.

```python
from typing import Annotated

import uvicorn

from byoconfig import BYOConfig

from my_app.asgi import asgi_app


class AppConfig(BYOConfig):
    port: Annotated[int, "uvicorn"] = 8889
    host: Annotated[str, "uvicorn"] = "127.0.0.1"
    log_level: Annotated[str, "uvicorn"] = "info"


def run_server():
    config = AppConfig()

    # Results in the dict: {'port': 8889, 'host': '127.0.0.1', 'log_level': 'info'}
    uvicorn_kwargs = config.get_by_annotated_type("uvicorn")

    uvicorn.run(asgi_app, **uvicorn_kwargs)
```

When given several annotations, `get_by_annotated_type` returns keys matching any of them. Pass `all_must_match=True` to only return keys matching all of them.

## Singleton

byoconfig comes with the `SingletonMetaclass` class.
This is useful in cases where dependency injection is difficult, like when using the `factory` design pattern.

```python
from byoconfig import BYOConfig, SingletonMetaclass


class SingletonConfig(BYOConfig, metaclass=SingletonMetaclass):
    test_1: str = "one"
    test_2: int = 0


def load_data():
    # Returns the instance created in __main__
    config = SingletonConfig()
    config.update({"test_2": 2})


if __name__ == "__main__":
    initial_config = SingletonConfig()
    load_data()
    print(initial_config.as_dict())
```

Will print:
```
{'test_1': 'one', 'test_2': 2}
```
