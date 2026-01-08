import logging
import platform
from os import environ
from re import compile
from typing import Optional

from byoconfig.error import BYOConfigError
from byoconfig.sources.base import BaseVariableSource

logger = logging.getLogger(__name__)


VALID_ENV_VAR = compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class EnvVariableSource(BaseVariableSource):
    """
    A VariableSource that loads data from environment variables.
    """

    def load_from_environment(
        self,
        selected_keys: list[str] = None,
        prefix: Optional[str] = None,
        trim_prefix: bool = True,
    ):
        if selected_keys and not prefix:
            return

        if selected_keys:
            if not all(isinstance(key, str) for key in selected_keys):
                invalid_keys = [
                    key for key in selected_keys if not isinstance(key, str)
                ]
                raise BYOConfigError(
                    f"Could not dump selected configuration data keys '{invalid_keys}' as environment variables "
                    "as they are not of type 'str'",
                    self,
                )
            missing_keys = {k for k in selected_keys if k not in environ}
            if missing_keys:
                raise BYOConfigError(
                    f"Could not load selected configuration data keys from environment: "
                    f"'{missing_keys}' environment variables are not defined.",
                    self,
                )

            data = {k.lower(): environ.get(k) for k in selected_keys}

            self.update(data)

            logger.debug(
                f"Loaded environment variables '{selected_keys}' as configuration data."
            )

        if not prefix:
            return

        if not isinstance(prefix, str):
            raise BYOConfigError("prefix must be a string", self)

        if prefix == "*":
            # We can ignore trim_prefix
            self.update(dict(environ))
            logger.debug("Loaded all environment variables as configuration data")

            return

        if not VALID_ENV_VAR.match(prefix):
            raise BYOConfigError(
                f"Could not load configuration data form environment: "
                f"env_prefix '{prefix}' must be a valid environment variable name",
                self,
            )

        try:
            # Windows stores environment variables keys as upper case.
            # We must convert the prefix to uppercase so we can match the case
            if platform.system() == "Windows":
                prefix = prefix.upper()

            data = self._get_by_prefix(dict(environ), prefix, trim_prefix)

            data = {k.lower(): v for k, v in data.items()}

        except Exception as e:
            raise BYOConfigError(
                f"Error occurred while loading env vars: {e.args}", self
            )

        self.update(data)
        logger.debug(f"Loaded environment variables with prefix: {prefix}")

    def dump_to_environment(
        self,
        selected_keys: list[str] = None,
        use_uppercase: bool = True,
        with_prefix: str = None,
    ):
        if selected_keys and not all(isinstance(key, str) for key in selected_keys):
            invalid_keys = [key for key in selected_keys if not isinstance(key, str)]
            raise BYOConfigError(
                f"Could not dump selected configuration data keys as environment variables: "
                f"Configuration data keys '{invalid_keys}' are not of type 'str'",
                self,
            )

        keys = self.keys()
        if selected_keys:
            keys = selected_keys
            missing_keys = [key for key in keys if key not in self.keys()]
            if missing_keys:
                raise BYOConfigError(
                    f"Could not dump selected configuration data keys as environment variables: "
                    f"Configuration data keys '{missing_keys}' are not defined",
                    self,
                )

        data = {k: self.get(k) for k in keys}

        if use_uppercase:
            with_prefix = with_prefix.upper() if with_prefix else None
            data = {k.upper(): v for k, v in data.items() if k}

        if not with_prefix:
            for k, v in data.items():
                environ[k] = str(v)

            return

        if not VALID_ENV_VAR.match(with_prefix):
            raise BYOConfigError(
                f"Invalid environment variable prefix '{with_prefix}'."
                f"Pattern must match '^[a-zA-Z_][a-zA-Z0-9_]*$'",
                self,
            )

        with_prefix = with_prefix.rstrip("_")
        try:
            data = {f"{with_prefix}_{k}": str(v) for k, v in data.items()}
            for k, v in data.items():
                environ[k] = str(v)
                print(environ[k])
        except Exception as e:
            raise e
