# BYOConfig

> Bring your own configuration

[![Tests Passing](https://github.com/camratchford/byoconfig/actions/workflows/lint_and_test.yml/badge.svg)](https://github.com/camratchford/byoconfig/actions/workflows/lint_and_test.yml)
[![Build](https://github.com/camratchford/byoconfig/actions/workflows/publish.yml/badge.svg)](https://github.com/camratchford/byoconfig/actions/workflows/publish.yml)
[![PyPi Version](https://img.shields.io/pypi/v/byoconfig)](https://pypi.org/project/byoconfig/)

## Features

- Loading/Dumping configuration data from/to:
  - YAML
  - TOML
  - JSON
- File format auto-detect and override options
- Ability to load configuration data from environment variables
- Allows hierarchical data to be loaded, then updated according to precedence rules.
- Extensible via plugins, allowing your own arbitrary data sources to be merged with config file and environment data.
- Configuration data available as class attributes (ex. `config.variable_1`)

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
