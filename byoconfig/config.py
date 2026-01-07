import logging
import inspect
from typing import Optional, Type

from byoconfig.sources import (
    BaseVariableSource,
    FileVariableSource,
    FileTypes,
    EnvVariableSource,
    SecretsManagerVariableSource,
)
from byoconfig.error import BYOConfigError

__all__ = ["Config"]


logger = logging.getLogger(__name__)


class Config(FileVariableSource, EnvVariableSource, SecretsManagerVariableSource):

    def __init__(self, **kwargs):
        self._metadata = self._metadata.union({name for name in self.__dir__()})

        self._var_source_name = kwargs.pop("config_name", None)
        self._assign_attrs = kwargs.pop("config_assign_attrs", False)
        super().__init__(**kwargs)
        try:
            self.update(kwargs)

        except BYOConfigError as e:
            raise e

        except FileNotFoundError as e:
            raise BYOConfigError(e.args, self)

        except ValueError as e:
            raise BYOConfigError(e.args, self)

        except Exception as e:
            raise BYOConfigError(f"An unhandled exception occurred during Config init: {e.args}", self)

    def include(self, plugin_class: Type[BaseVariableSource], **kwargs):
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
            self.set(plugin.get())
            logger.debug(
                f"Initialized plugin '{plugin_class.__name__}' with data: {plugin.get()}"
            )

        except BYOConfigError as e:
            raise e

        except Exception as e:
            raise e
