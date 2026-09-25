import logging
import platform
from os import environ
from re import compile
from typing import Any, Optional

from byoconfig.sources.base import BaseVariableSource

logger = logging.getLogger(__name__)


VALID_ENV_VAR = compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class EnvVariableSource(BaseVariableSource):
    """
    A VariableSource that loads data from environment variables.
    """

    _env_prefix: str | None = None

    def load_from_environment(
        self,
        prefix: Optional[str] = None,
        trim_prefix: bool = True,
    ):

        if not prefix:
            return

        if not isinstance(prefix, str):
            raise TypeError("prefix must be a string")

        if prefix == "*":
            # We can ignore trim_prefix
            self._update_skip_invalid({k.lower(): v for k, v in environ.items()})
            logger.debug("Loaded all environment variables as configuration data")

            return

        if not VALID_ENV_VAR.match(prefix):
            raise ValueError(
                f"Could not load configuration data form environment: "
                f"env_prefix '{prefix}' must be a valid environment variable name"
            )

        # Windows stores environment variables keys as upper case.
        # We must convert the prefix to uppercase so we can match the case
        if platform.system() == "Windows":
            prefix = prefix.upper()

        data = self._get_by_prefix(dict(environ), prefix, trim_prefix)
        data = {k.lower(): v for k, v in data.items()}

        self._update_skip_invalid(data)
        logger.debug(f"Loaded environment variables with prefix: {prefix}")

    def dump_to_environment(
        self,
        selected_keys: list[str] = None,
        use_uppercase: bool = True,
        with_prefix: str | None = None,
    ):
        if selected_keys and not all(isinstance(key, str) for key in selected_keys):
            invalid_keys = [key for key in selected_keys if not isinstance(key, str)]
            raise TypeError(
                f"Could not dump selected configuration data keys as environment variables: "
                f"Configuration data keys '{invalid_keys}' are not of type 'str'"
            )

        keys = self.keys()
        if selected_keys:
            keys = selected_keys
            missing_keys = [key for key in keys if key not in self.keys()]
            if missing_keys:
                raise KeyError(
                    f"Could not dump selected configuration data keys as environment variables: "
                    f"Configuration data keys '{missing_keys}' are not defined"
                )

        data = {k: self.get(k) for k in keys}

        if use_uppercase:
            with_prefix = with_prefix.upper() if with_prefix else ""
            data = {k.upper(): v for k, v in data.items() if k}

        if not with_prefix:
            self._set_environment_variables(data)
            return

        if not VALID_ENV_VAR.match(with_prefix):
            raise ValueError(
                f"Invalid environment variable prefix '{with_prefix}'."
                f"Pattern must match '^[a-zA-Z_][a-zA-Z0-9_]*$'"
            )

        with_prefix = with_prefix.rstrip("_") + "_" if with_prefix else ""
        data = {f"{with_prefix}{k}": v for k, v in data.items()}
        self._set_environment_variables(data)

    @staticmethod
    def _set_environment_variables(data: dict[str, Any]):
        for name, value in data.items():
            try:
                environ[name] = str(value)
            except (ValueError, OSError) as error:
                raise ValueError(
                    f"Could not set environment variable '{name}': {error}"
                ) from error
