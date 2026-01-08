from byoconfig.sources.base import BaseVariableSource
from byoconfig.config import Config
from byoconfig.singleton import SingletonConfig


class ASubClassOfSingletonConfig(SingletonConfig):
    def __init__(self, **kwargs):
        self.set("var3", 3)
        super().__init__(**kwargs)



def new_instance_of_singleton():
    return ASubClassOfSingletonConfig(var2=2)


class PluginVarSource(BaseVariableSource):
    def __init__(self, plugin_kwarg: str):
        self.name = 'PluginVarSource'
        self._data = {
            "test_var1": 'from plugin #1',
            "test_var2": 'from plugin #2',
            "plugin_kwarg": plugin_kwarg
        }



class ConfigWithClassAttrs(Config):
    a_class_var = "I hope this works"