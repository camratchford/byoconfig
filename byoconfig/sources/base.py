
import logging
import re

from typing import Any, Type
from collections.abc import Hashable

from byoconfig.error import BYOConfigError

logger = logging.getLogger(__name__)

# Runs once, produces an efficient mapping that converts invalid characters to underscores
# invalid_character_list = [i for i in filter(lambda x: not str.isidentifier(x), (chr(i) for i in range(0, 96)))]
# translate_map = {
#     ord(invalid_char): ord("_")
#     for invalid_char in invalid_character_list
# }

# For use with str.translate: Converts characters not valid inside a Python identifier to an underscore.
translate_map = {
    0: 95, 1: 95, 2: 95, 3: 95, 4: 95, 5: 95, 6: 95, 7: 95, 8: 95, 9: 95, 10: 95, 11: 95, 12: 95, 13: 95,
    14: 95, 15: 95, 16: 95, 17: 95, 18: 95, 19: 95, 20: 95, 21: 95, 22: 95, 23: 95, 24: 95, 25: 95, 26: 95,
    27: 95, 28: 95, 29: 95, 30: 95, 31: 95, 32: 95, 33: 95, 34: 95, 35: 95, 36: 95, 37: 95, 38: 95, 39: 95,
    40: 95, 41: 95, 42: 95, 43: 95, 44: 95, 45: 95, 46: 95, 47: 95, 48: 95, 49: 95, 50: 95, 51: 95, 52: 95,
    53: 95, 54: 95, 55: 95, 56: 95, 57: 95, 58: 95, 59: 95, 60: 95, 61: 95, 62: 95, 63: 95, 64: 95, 91: 95,
    92: 95, 93: 95, 94: 95
}


def convert_to_valid_identifier(invalid_str: str):
    """
    Converts a string that has characters that would throw errors if it were used as a class attribute identifier.
    Invalid characters are converted to underscores. Sequences of 2 or more underscores are collapsed into a single '_'.
      One bonus side effect of this is that it will prevent the output from matching any magic identifiers such as
      '__init__' or '__sub__'
    """
    valid_str = invalid_str.translate(translate_map)

    max_underscores = len(valid_str)
    dedup_underscore_pattern = "_{2," + str(max_underscores) + "}"
    deduped_underscore_str = re.sub(dedup_underscore_pattern, "_", valid_str)
    removed_leading_underscore = deduped_underscore_str.lstrip("_")

    return removed_leading_underscore


class BaseVariableSource:
    """
    The base for other variable source object.
      - Provides methods to load and retrieve data from different sources.
      - Borrows heavily from collections.UserDict

    Attrs:
        _var_source_name (str):
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

    _var_source_name: str = ""
    _assign_attrs: bool = False
    _metadata: set[str] = {"_var_source_name", "_metadata", "_assign_attrs", "_data"}
    _data: dict[str, Any] = {}

    def _is_valid_key_name(self, key: str):
        return not key.startswith("_") and key not in self._metadata

    def _sanitized_data(self) -> dict:
        return {k: v for k, v in filter(lambda key_val: self._is_valid_key_name(key_val[0]), self._data.items())}

    def _sanitized_attrs(self):
        return {k: v for k, v in filter(lambda key_val: self._is_valid_key_name(key_val[0]), self.__dict__.items())}

    def get(self, key: str, default: Any = None):
        if key in self._sanitized_data():
            return self._data[key]
        return default

    @staticmethod
    def _get_keys_by_prefix(data: dict[str, Any], prefix: str, trim_prefix: bool = True) -> list[str]:
        return [
            k.replace(f"{prefix}_", "") if trim_prefix else k
            for k in data.keys()
        ]

    def _get_by_prefix(self, data: dict[str, Any], prefix: str, trim_prefix: bool = True) -> dict[str, Any]:
        return {
            k.replace(f"{prefix}_", "") if trim_prefix else k: data.get(k)
            for k in self._get_keys_by_prefix(data, prefix, False)
        }

    def get_by_prefix(self, prefix: str, trim_prefix: bool = True) -> dict[str, Any]:

        return self._get_by_prefix(self._sanitized_data(), prefix, trim_prefix)

    def set(self, key: str, value: Any):
        if not self._is_valid_key_name(key):
            message = "Run `print(Config._metadata)` for a full list of reserved key names."
            if key.startswith("_"):
                message = "Key names must not start with underscore '_'. "
            raise BYOConfigError(
                f"Invalid configuration data key name. Key is reserved for BYOConfig internals: {message}"
                , self
            )

        self._data[key] = value

        if not self._assign_attrs:
            return

        self.__setattr__(key, value)

    def update(self, data: dict[str, Any] = None, **kwargs):
        if data and kwargs:
            data.update(kwargs)

        values = data or kwargs or None

        if not values:
            return

        for k, v in data.items():
            self.set(k, v)

    def delete_item(self, key: str):
        del self._data[key]

        if not self._assign_attrs:
            return

        if self.get(key):
            delattr(self, key)

    def clear_data(self, *keys: str):
        keys = keys if keys else self._data.keys()

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

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, key):
        return key in self._data

    def __repr__(self):
        return (
            f"{self.__class__.__name__}: {self._var_source_name}"
        )

    def __str__(self):
        return self.__repr__()

    def __setattr__(self, key, value):
        if not key.isidentifier():
            key = convert_to_valid_identifier(key)
        super().__setattr__(key, value)

