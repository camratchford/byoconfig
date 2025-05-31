from byoconfig.sources.base import BaseVariableSource
from byoconfig.sources.file import FileVariableSource, FileTypes
from byoconfig.sources.env import EnvVariableSource


class NameSource(BaseVariableSource):
    def __init__(self, name: str = "", var_source_name: str = "NameSource", precedence: int = 1, **kwargs):
        self._var_source_name = var_source_name
        self._precedence = precedence
        self.load(name)
        self._should_not_appear = 'should_not_appear'
        self.should_appear = 'should_appear'

    def load(self, name: str):
        self.set_data({'name': name})


class GenericFileSource(FileVariableSource):
    def __init__(self, source_file: str, forced_file_type: FileTypes = None, **kwargs):
        super().__init__(source_file=source_file, forced_file_type=forced_file_type, **kwargs)
        self._var_source_name = 'GenericFileSource'
        self._precedence = 1


class GenericEnvSource(EnvVariableSource):
    def __init__(self, env_prefix: str, **kwargs):
        super().__init__(env_prefix=env_prefix, **kwargs)
        self._var_source_name = 'GenericEnvSource'
        self._precedence = 1


class PluginVarSource(BaseVariableSource):
    def __init__(self, plugin_kwarg: str):
        self._var_source_name = 'PluginVarSource'
        self._precedence = 1
        self.test_var1 = 'from plugin #1'
        self.test_var2 = 'from plugin #2'
        self.plugin_kwarg = plugin_kwarg

