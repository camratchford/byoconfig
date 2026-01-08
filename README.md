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
# imagining the contents of config.yaml are:
important_path: path/that/must/exists
"""

# Auto-detects the file type based on file extension suffix
conf = Config('path/to/config.yaml')

# Alternatively, specify a forced_file_type argument (One of 'YAML', 'TOML', or 'JSON'
# conf = Config("path/to/config", forced_file_extension="YAML")

def ensure_file(path: str):
    Path(path).mkdir(parents=True)

if __name__ == "__main__":
    # The configuration variable is accessible by the instance attribute conf.important_path
    ensure_file(conf.important_path)

```

### From Environment Variables

```python

from byoconfig import Config

conf = Config(env_prefix="MY_APP")

# Imagining that you have an env var `MY_APP_var_1` set
print(conf.var_1)

# If you want to load all of the environment variables, use the '*' wildcard as env_prefix

conf2 = Config(env_prefix="*")

print(conf2.PATH)

```


### From Custom plugins

```python

from byoconfig.sources import BaseVariableSource
from byoconfig import Config


# Subclass the BaseVariableSource class
class MyVarSource(BaseVariableSource):
  def __init__(self, init_options):
    # Using an imaginary function 'get_external_data' in place of something like an http request or DB query
    self.external_data = get_external_data(init_options)

    # Initializes the class attrs, making the data availalble via MyVarSource.var_name  
    self.set(self.external_data)


# Start with a config object, containing the data from any source (optional)
my_config = Config("some/file/data.json")

# Include your plugin, merging the data from MyVarSource and the config object above
# You can pass kwargs to include as if you're passing them to MyVarSource's __init__ method.
my_config.include(MyVarSource, init_options="some data to initialize your custom data source")

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
conf.dump_to_file("running_config", forced_file_type="TOML")

```
