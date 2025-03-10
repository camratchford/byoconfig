import logging
import platform
from os import environ
from re import compile
from typing import Optional

from byoconfig.sources.base import BaseVariableSource
from byoconfig.error import BYOConfigError

logger = logging.getLogger(__name__)


VALID_ENV_VAR = compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class EnvVariableSource(BaseVariableSource):
    """
    A VariableSource that loads data from environment variables.
    """

    def __init__(self, env_prefix: Optional[str] = None, **kwargs):
        """
        Initialize an EnvVariableSource instance.

        Args:
            env_prefix (str):
                The configuration keys will be loaded from the environment variables with this prefix.
                Use the "*" wildcard if you want to load all environment variables as configuration keys.
            **kwargs:
                So that interface is consistent with other VariableSource classes.

        """
        try:
            self.load_env(env_prefix)
        except BYOConfigError as e:
            raise e
        if env_prefix:
            logger.debug(f"Loaded environment variables with prefix: {env_prefix}")

    def load_env(self, env_prefix: Optional[str] = None):
        """
        Load environment variables with optional prefix.

        Args:
            env_prefix (str):
                The configuration keys will be loaded from the environment variables with this prefix.
                Use the "*" wildcard if you want to load all environment variables as configuration keys.
        """

        if env_prefix is None:
            return

        if not isinstance(env_prefix, str):
            raise BYOConfigError("env_prefix must be a string", self)

        if env_prefix == "*":
            data = environ
            self.set_data(data)
            return

        if not VALID_ENV_VAR.match(env_prefix):
            raise BYOConfigError(
                f"env_prefix '{env_prefix}' must be a valid environment variable name",
                self,
            )

        prefix = env_prefix
        if not env_prefix.endswith("_"):
            prefix = env_prefix + "_"
        try:
            if platform.system() == "Windows":
                prefix = prefix.upper()
            data = {k.replace(prefix, ""): v for k, v in environ.items() if prefix in k}

        except Exception as e:
            msg = e.args[0]
            raise BYOConfigError(f"Error occurred while loading env vars: {msg}", self)

        self.set_data(data)
