from byoconfig.config import Config
from byoconfig.sources.base import BaseVariableSource


class PluginVarSource(BaseVariableSource):
    def __init__(self, plugin_kwarg: str):
        self.name = 'PluginVarSource'
        self._data = {
            "test_var1": 'from plugin #1',
            "test_var2": 'from plugin #2',
            "plugin_kwarg": plugin_kwarg
        }


class ConfigWithClassAttrs(Config):
    class_attr_1 = 1


class ConfigWithInstanceAttrs(Config):
    def __init__(self, **kwargs):
        self.instance_var_1 = 1
        super().__init__(**kwargs)

