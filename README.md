# BYOConfig

> Bring your own configuration

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

```python
from pathlib import Path

from byoconfig import Config

"""
# imagining the contents of config.yaml are:
important_path: path/that/must/exists
"""
conf = Config('path/to/config.yaml')

def ensure_file(path: str):
    Path(path).mkdir(parents=True)

if __name__ == "__main__":
    # The configuration variable is accessible by the instance attribute conf.important_path
    ensure_file(conf.important_path)

```

## Loading plugins

```python

from byoconfig.sources import BaseVariableSource
from byoconfig import Config

# Subclass the BaseVariableSource class
# (unless you require the methods unique to FileVariableSource or EnvVariableSource classes)
class MyVarSource(BaseVariableSource):
    def __init__(self, init_options):
        # Using an imaginary function 'get_external_data' in place of something like an http request or DB query
        self.external_data = get_external_data(init_options)
        
        # Initializes the class attrs, making the data availalble via MyVarSource.var_name  
        self.set_data(self.external_data)

# Start with a config object, containing the data from any source (optional)
my_config = Config("some/file/data.json")

# Include your plugin, merging the data from MyVarSource and the config object above
# You can pass kwargs to include as if you're passing them to MyVarSource's __init__ method.
my_config.include(MyVarSource, init_options={'init_options': 'data'})
```

