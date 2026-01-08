import logging
import re
from re import compile
from typing import Any

from byoconfig.error import BYOConfigError

logger = logging.getLogger(__name__)

# Generate the list of ASCII characters that are invalid for use in a Python identifier string
invalid_character_list = [
    i for i in filter(lambda x: not str.isidentifier(x), (chr(i) for i in range(0, 96)))
]

# For use with str.translate: Converts characters not valid inside a Python identifier to an underscore.
translate_map = {ord(invalid_char): ord("_") for invalid_char in invalid_character_list}


def convert_to_valid_identifier(invalid_str: str):
    """
    Converts a string that has characters that would throw errors if it were used as a class attribute identifier.
    Invalid characters are converted to underscores. Sequences of 2 or more underscores are collapsed into a single '_'.
      One bonus side effect of this is that it will prevent the output from matching any magic identifiers such as
      '__init__' or '__sub__'
    """
    valid_str = invalid_str.translate(translate_map)

    max_underscores = len(valid_str)
    dedup_underscore_pattern = compile("_{2," + str(max_underscores) + "}")
    deduped_underscore_str = dedup_underscore_pattern.sub("_", valid_str)
    removed_leading_underscore = deduped_underscore_str.lstrip("_")

    return removed_leading_underscore


class BaseVariableSource:
    """
    The base for other variable source object.
      - Provides methods to load and retrieve data from different sources.
      - Borrows from collections.UserDict

    Attrs:
        name (str):
            The name of the variable source. Must be unique for each instance.

        _assign_attrs: (bool):
            If true, the contents of self.data will be assigned to instance attributes.
            Ex. If 'var_source.data' is '{"verbose": True}', then the BaseVariableSource instance will have an attribute
            'verbose' (var_source.verbose) with a value of True .

        _metadata:
            Attributes that:
              - Are not listed in data when `.get()` is executed.
              - Are not permitted as configuration data when `.set()` is executed.
            When creating a subclass of BaseVariableSource, add any attributes that
              should not be imported or exported to this set.
    """

    name: str = ""
    _assign_attrs: bool = False
    _metadata: set[str] = {"name", "_metadata", "_assign_attrs", "_data"}
    _data: dict[str, Any] = {}

    def _is_valid_key_name(self, key: str):
        return not key.startswith("_") and key not in self._metadata

    def _sanitized_data(self) -> dict:
        return {
            k: v
            for k, v in filter(
                lambda key_val: self._is_valid_key_name(key_val[0]), self._data.items()
            )
        }

    def _sanitized_attrs(self):
        return {
            k: v
            for k, v in filter(
                lambda key_val: self._is_valid_key_name(key_val[0]),
                self.__dict__.items(),
            )
        }

    def get(self, key: str, default: Any = None):
        if key in self._sanitized_data():
            return self._data[key]

        return default

    @staticmethod
    def _get_keys_by_prefix(
        data: dict[str, Any], prefix: str, trim_prefix: bool = True
    ) -> list[str]:
        trim_pattern = re.compile(f"({prefix}_?)")

        return [
            trim_pattern.sub("", k) if trim_prefix else k
            for k in data.keys()
            if k.startswith(prefix)
        ]

    @staticmethod
    def _get_by_prefix(
        data: dict[str, Any], prefix: str, trim_prefix: bool = True
    ) -> dict[str, Any]:
        trim_pattern = re.compile(f"({prefix}_?)")

        return {
            trim_pattern.sub("", k) if trim_prefix else k: v
            for k, v in data.items()
            if k.startswith(prefix)
        }

    def get_by_prefix(self, prefix: str, trim_prefix: bool = True) -> dict[str, Any]:
        return self._get_by_prefix(self._sanitized_data(), prefix, trim_prefix)

    def set(self, key: str, value: Any):
        if not self._is_valid_key_name(key):
            message = (
                "Run `print(Config._metadata)` for a full list of reserved key names."
            )
            if key.startswith("_"):
                message = "Key names must not start with underscore '_'. "
            raise BYOConfigError(
                f"Invalid configuration data key name '{str(key)}'. Key is reserved for BYOConfig internals: {message}",
                self,
            )

        self._data[key] = value

        if not self._assign_attrs:
            return

        self.__setattr__(key, value)

    def update(self, data: dict[str, Any] = None, /, **kwargs):
        values = {}
        if data is not None:
            values = data
        if kwargs:
            values = kwargs

        if not values:
            return

        for k, v in values.items():
            self.set(k, v)

    def delete_item(self, key: str):
        del self._data[key]

        if not self._assign_attrs:
            return

        delattr(self, key)

    def clear_data(self, *keys: str):
        keys = keys if keys else self._data.copy().keys()

        for key in keys:
            if key not in self._data:
                continue
            del self._data[key]

        if not self._assign_attrs:
            return

        for attr in keys:
            if not self._is_valid_key_name(attr) or not hasattr(self, attr):
                continue
            delattr(self, attr)

    def keys(self):
        return [i for i in self._sanitized_data().keys()]

    def values(self):
        return [i for i in self._sanitized_data().values()]

    def items(self):
        return [i for i in self._sanitized_data().items()]

    def as_dict(self, copy: bool = True):
        return self._data.copy() if copy else self._data

    def __init_subclass__(cls, **kwargs):
        """
        Ensures that subclasses can add class attributes as configuration data, expecting to access
        it via .get("class_attr_name") or .as_dict()["class_attr_name"]
        """
        cls._data.update(
            {k: v for k, v in cls.__dict__.items() if cls._is_valid_key_name(cls, k)}
        )

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, key):
        return key in self._data

    def __repr__(self):
        return f"{self.__class__.__name__}: {self.name}"

    def __str__(self):
        return self.__repr__()

    def __setattr__(self, key, value):
        if not key.isidentifier():
            key = convert_to_valid_identifier(key)
        super().__setattr__(key, value)
