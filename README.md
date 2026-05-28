# BYOConfig

> Bring your own configuration

A dependency injection configuration class supporting multiple file formats, environment variables, AWS Secrets Manager, singletons, and more.

## Features

- Loading/Dumping configuration data using:
  - YAML
  - TOML
  - JSON
  - Environment Variables
- Loading secrets from AWS Secrets Manager
- File type detection
- Imported value type conversion to `pathlib.Path`, `datetime.datetime`, `datetime.date`
- Filtering configuration data by key name prefix
- Filtering configuration data by a `typing.Annotated` type.

## Installing

```bash
pip install byconfig
```

## Usage


### From file

```python
from pathlib import Path

from byoconfig import Config

"""
# path/to/config.yaml
important_path: path/that/must/exists
"""

# Auto-detects the file type based on file extension suffix, assigns all top-level configuration data as object attributes.
conf = Config(file_path='path/to/config.yaml')

# Alternatively, specify a forced_file_type argument (One of 'YAML', 'TOML', or 'JSON'
# conf = Config("path/to/config", forced_file_extension="YAML")

def ensure_file(path: str):
    Path(path).mkdir(parents=True)

if __name__ == "__main__":
    # The configuration variable is accessible by the instance attribute conf.important_path
    ensure_file(conf.get("important_path"))

```

### From Environment Variables

```python
from os import environ

from byoconfig import Config

# Environment variables are always stored as strings
environ.update({"MY_APP_VAR_1": "1", "TEST_SOMETHING_SOMETHING": "2"})

conf = Config(env_prefix="MY_APP")

print(conf.get("var_1"))
# > "1"

# To run the environment loader again
conf.load_from_environment(prefix="TEST")
print(conf.get("something_something"))
# > "2"

# If you want to load all the environment variables, use the '*' wildcard as env_prefix
conf2 = Config(env_prefix="*")
print(conf2.PATH)

```


### From AWS Secrets Manager

```python

from byoconfig import Config


# ~/.aws/credentials (Where the values provided are not foo, bar, baz but actual authentication parameters)
# See https://boto3.amazonaws.com/v1/documentation/api/1.9.46/guide/configuration.html#configuring-credentials
"""
[default]
aws_access_key_id=foo
aws_secret_access_key=bar
aws_session_token=baz
"""

# AWS Secrets Manager secrets, using the JSON option.
# Try not to let your top-level JSON keys overlap, as the two resulting dicts will be merged. 
"""
# Where the name of the secret is api_keys/important
{
    "important_api_key": "B3U1+L/ZLKfFfdLf+cdx/7f9HhMjiL6meZlS11RlojQ",
}

# Where the name of the secret is api_keys/different
{
    "different_api_key": "Jc6Qq37sV+3SidDmkQ42RXtq1x7qEAQUZKCVr7JzADM",
}
"""

class ImportantAPIClient:
    def __init__(self, config: Config):
        self.api_key = config.get("important_api_key")

class DifferentAPIClient:
    def __init__(self, config: Config):
        self.api_key = config.get("different_api_key")

def main():
    config = Config(aws_secret_name="api_keys/important") 
    important_api_client = ImportantAPIClient(config)
    
    # Should you need to load more than 1 secret, there's a method available.
    config.load_from_secrets_manager("api_keys/different")
    different_api_client = DifferentAPIClient(config)

```


### Loading Arbitrary Values

```python
from byoconfig import Config

# Via kwargs
conf = Config(my_var="abc", my_var_2=123)

# Via the set_data method / data property
conf.set({"my_var": "abc"})
# Equivalent to
conf.data = {"my_var": "abc"}

```


### Dumping Data

An example of dumping the contents of your config to a file.

```python
from byoconfig import Config

conf = Config()

# We can pretend that you've loaded your configuration data in conf, and you'd like it output to a file
# to be used later
...

# Auto-detects the file-type based on file extension suffix
conf.dump_to_file("running_config.yml")
# Overriding the auto-detect in case you have no extension
conf.dump_to_file("running_config", forced_type="TOML")
```

An example of excluding configuration data from the `dump_to_file` method output.

```python
from typing import Annotated

from byoconfig import Config

# Create a subclass of Config
class MyConfig(Config):
    # The type annotation must appear in the class body and must be assigned a value. For example: None or "" 
    not_critically_secret_data: str = "This can be exported to file"
    super_secret_data: Annotated[str, "excluded"] = ""

# Initialize your instance, defining the value of your super secret data. Like an API key or something you don't want to share.
config = MyConfig(env_selected_keys=['super_secret_data'])
# The contents of the resulting file will not contain 'super_secret_data' or any data annotated with "excluded"
config.dump_to_file("my_config.json")
```

### Filtering Data

#### By Key Name Prefix

We can group our configuration data by the kwargs for a function/method/class, prefixing each parameter with a name.

Using `uvicorn` as the prefix to supply kwargs to `uvicorn.run`:

```python

import uvicorn
from byoconfig import Config

# like fastapi or starlette
from my_app.asgi import asgi_app


class AppConfig(Config):
    uvicorn_port = 8889
    uvicorn_host = "127.0.0.1"
    uvicorn_log_level = "info"


def run_server():
    config = AppConfig()
    
    # Results in the dict: {'port': 8889, 'host': '127.0.0.1', 'log_level': 'info'}
    uvicorn_kwargs = config.get_by_prefix("uvicorn", trim_prefix=True)
    
    uvicorn.run(asgi_app, **uvicorn_kwargs)

```

#### By Annotated Type

We can group our configuration data in arbitrary categories by supplying a type annotation via `typing.Annotated`

Same example as before, but with annotations.

```python
from typing import Annotated

import uvicorn
from byoconfig import Config

from my_app.asgi import asgi_app


class AppConfig(Config):
    port: Annotated[int, "uvicorn"] = 8889
    host: Annotated[str, "uvicorn"]  = "127.0.0.1"
    log_level: Annotated[str, "uvicorn"]  = "info"


def run_server():
    config = AppConfig()
    
    # Results in the dict: {'port': 8889, 'host': '127.0.0.1', 'log_level': 'info'}
    uvicorn_kwargs = config.get_by_annotated_type("uvicorn")
    
    uvicorn.run(asgi_app, **uvicorn_kwargs)
```


## Singleton

byoconfig comes with the `SingletonMetaclass` class.
This is useful in cases where dependency injection is difficult, like when using the `factory` design pattern.

```python
from byoconfig import Config, SingletonMetaclass


class SingletonConfig(Config, metaclass=SingletonMetaclass):
    test_1 = "one"


def load_data():
    # Running __init__ will return the initial instance from __main__
    config = SingletonConfig()
    # test_2 is overwritten, test_3 is added
    more_data = {"test_2": 2, "test_3": "III"}
    config.update(more_data)


if __name__ == "__main__":
    initial_config = SingletonConfig(test_2="two", test_4="0100")
    load_data()
    print(initial_config.as_dict())
```

Will return (not guaranteed to be in the same order):
```
{'test_1': 'one', 'test_2': 2, 'test_4': '0100', 'test_3': 'III'}
```

