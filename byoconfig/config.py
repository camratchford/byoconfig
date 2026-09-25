import logging

from byoconfig.sources import (
    EnvVariableSource,
    FileVariableSource,
    SecretsManagerVariableSource,
)

__all__ = ["BYOConfig"]


logger = logging.getLogger(__name__)


class BYOConfig(
    FileVariableSource, EnvVariableSource, SecretsManagerVariableSource
): ...
