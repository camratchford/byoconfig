import logging
from typing import Type
from inspect import ismethod

from byoconfig.sources import (
    BaseVariableSource,
    FileVariableSource,
    EnvVariableSource,
    SecretsManagerVariableSource,
)
from byoconfig.error import BYOConfigError

__all__ = ["Config"]


logger = logging.getLogger(__name__)


class Config(FileVariableSource, EnvVariableSource, SecretsManagerVariableSource):
    """
    Load order: (Subsequent entries overwrite the previous)
    1. File
    2. Environment Variables
    3. AWS Secrets Manager
    4. The `config_data` parameter
    5. The `kwargs` parameter
    """

    def __init__(self, **kwargs):
        self._metadata = self._metadata.union(
            {name for name in self.__dir__() if ismethod(getattr(self, name))}
        )

        self.name = kwargs.pop("config_name", self.__class__.__name__)
        self._assign_attrs = kwargs.pop("config_assign_attrs", False)
        self.update(**kwargs.pop("config_data", {}))
        if kwargs:
            load_from_file_kwargs = {
                k: kwargs.pop(f"file_{k}")
                for k, v in self._get_by_prefix(kwargs, "file", True).items()
            }
            self.load_from_file(**load_from_file_kwargs)
        if kwargs:
            load_from_env_kwargs = {
                k: kwargs.pop(f"env_{k}")
                for k, v in self._get_by_prefix(kwargs, "env", True).items()
            }

            self.load_from_environment(**load_from_env_kwargs)
        if kwargs:
            load_from_secrets_manager_kwargs = {
                k: kwargs.pop(k)
                for k, v in self._get_by_prefix(kwargs, "aws", False).items()
            }
            self.load_from_secrets_manager(**load_from_secrets_manager_kwargs)

        if kwargs:
            init_kwarg_prefixes = {"config", "file", "env", "aws"}
            update_kwargs = {
                k: v
                for k, v in kwargs.items()
                if not any(k.startswith(prefix) for prefix in init_kwarg_prefixes)
            }
            self.update(**update_kwargs)

    def include(self, plugin_class: Type[BaseVariableSource], **kwargs):
        try:
            plugin = plugin_class(**kwargs)  # type: ignore
            self.update(**plugin.as_dict())
            logger.debug(
                f"Initialized plugin '{plugin_class.__name__}' with data: {plugin.as_dict()}"
            )

        except BYOConfigError as e:
            raise e

        except Exception as e:
            raise e
