import logging
import inspect
from typing import Optional, Type

from byoconfig.sources import (
    BaseVariableSource,
    FileVariableSource,
    EnvVariableSource,
    FileTypes,
)
from byoconfig.error import BYOConfigError

__all__ = ["Config"]

logger = logging.getLogger(__name__)


class Config(FileVariableSource, EnvVariableSource):
    """
    A versatile config object that can parse many file types, load environment variables,
    and load dictionary keys as class attributes.
      - Multiple config objects from different unique sources can be collated easily with a precedence value.
      - Config instances with higher precedence have their values overwrite the values of lower precedence
        instances when merging objects.
    """

    def __init__(
        self,
        source_file_path: Optional[str] = None,
        forced_file_type: Optional[FileTypes] = None,
        env_prefix: Optional[str] = None,
        var_source_name: Optional[str] = "Config",
        precedence: Optional[int] = 1,
        **kwargs,
    ):
        """
        Initialize a Config object.

        Args:
            source_file_path (str):
                The path to the source file.

            forced_file_type (FileTypes):
                The file type of the source file, if you don't want to use the file's extension.

            var_source_name (str):
                The name of the variable source.

            env_prefix (str):
                The configuration keys will be loaded from the environment variables with this prefix.
                Use the "*" wildcard if you want to load all environment variables as configuration keys.

            precedence (int):
                The precedence of the variable source.

            **kwargs:
                Arbitrary keyword arguments, to be loaded as class attributes.
        """
        try:
            self._precedence = precedence
            self._var_source_name = var_source_name
            super().__init__(
                source_file=source_file_path, forced_file_type=forced_file_type
            )
            super().load_env(env_prefix)

            self.set_data(kwargs)
            logger.debug(
                f"Config object {self._var_source_name} created with precedence {self._precedence}"
            )

        except BYOConfigError as e:
            raise e

        except FileNotFoundError as e:
            raise e

        except ValueError as e:
            raise e

        except Exception as e:
            raise e

    def include(self, plugin_class: Type[BaseVariableSource], **kwargs):
        """
        Include a plugin class in the config object.

        Args:
            plugin_class (Type[BaseVariableSource]):
                The plugin class to include in the config object.

            **kwargs:
                Arbitrary keyword arguments to pass to the plugin class.
        """
        try:
            # get signature of plugin class
            sig = inspect.signature(plugin_class)
            # Compare kwargs to signature
            for k, v in kwargs.items():
                if k not in sig.parameters:
                    raise BYOConfigError(
                        f"Invalid parameter '{k}' for plugin class '{plugin_class.__name__}'",
                        self,
                    )
            plugin = plugin_class(**kwargs)  # type: ignore
            self.set_data(plugin.get_data())
            logger.debug(
                f"Initialized plugin '{plugin_class.__name__}' with data: {plugin.get_data()}"
            )

        except BYOConfigError as e:
            raise e

        except Exception as e:
            raise e
