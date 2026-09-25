import logging
import re
from inspect import isdatadescriptor, isroutine
from typing import Any, get_type_hints

logger = logging.getLogger(__name__)


class BaseVariableSource:
    def _is_valid_key_name(self, key: str):
        if key.startswith("_"):
            return False
        if key in self.__dict__:
            return True
        if key not in self.__class__.__dict__:
            return False
        class_value = self.__class__.__dict__[key]
        return not (isroutine(class_value) or isdatadescriptor(class_value))

    @property
    def _accssible_data(self):
        # Ensure we get both instance and class attrs, and that instance attrs take precedence.
        data = {**self.__class__.__dict__, **self.__dict__}
        return {k: v for k, v in data.items() if self._is_valid_key_name(k)}

    def get(self, key: str, default: Any = None):
        return self._accssible_data.get(key, default)

    @staticmethod
    def _get_by_prefix(
        data: dict[str, Any],
        prefix: str,
        trim_prefix: bool = True,
        case_sensitive: bool = True,
    ) -> dict[str, Any]:
        flags = 0 if case_sensitive else re.IGNORECASE
        trim_pattern = re.compile(f"(^{prefix}_?)", flags=flags)
        return {
            trim_pattern.sub("", k) if trim_prefix else k: v
            for k, v in data.items()
            if trim_pattern.match(k)
        }

    def get_by_prefix(self, prefix: str, trim_prefix: bool = True) -> dict[str, Any]:
        return self._get_by_prefix(self._accssible_data, prefix, trim_prefix)

    @classmethod
    def get_type_annotations(cls) -> dict[str, tuple[type[Any] | str, ...]]:
        try:
            type_hints = {
                name: [typ, *getattr(typ, "__metadata__", ())]
                for name, typ in get_type_hints(cls, include_extras=True).items()
            }

            return type_hints

        except TypeError:
            raise

    def get_by_annotated_type(self, *annotations: Any, all_must_match=False):
        type_hints = self.get_type_annotations()

        if not type_hints:
            return {}

        annotation_filter = all if all_must_match else any

        return {
            attr_name: self.get(attr_name)
            for attr_name in type_hints.keys()
            if annotation_filter(
                annotation in type_hints[attr_name] for annotation in annotations
            )
        }

    def set(self, key: str, value: Any):
        if key not in self._accssible_data:
            raise KeyError(f"No attr with name {key}")
        setattr(self, key, value)

    def _update_skip_invalid(self, data: dict[str, Any] = None, /, **kwargs):
        values = {}
        if data is not None:
            values = data
        if kwargs:
            values = kwargs

        if not values:
            return

        for key, value in values.items():
            if not self._is_valid_key_name(key):
                continue

            self.set(key, value)

    def update(self, data: dict[str, Any] = None, /, **kwargs):
        values = data if data is not None else {}
        if kwargs:
            values = kwargs
        if not values:
            return
        for key, value in values.items():
            self.set(key, value)

    def delete_item(self, key: str):
        if key in self.__dict__ and self._is_valid_key_name(key):
            delattr(self, key)

    def clear_data(self, *keys: str):
        keys = keys if keys else self._accssible_data.keys()

        for key in keys:
            if key not in self._accssible_data:
                continue
            self.delete_item(key)

    def keys(self):
        return self._accssible_data.keys()

    def values(self):
        return self._accssible_data.values()

    def items(self):
        return self._accssible_data.items()

    def as_dict(self):
        return self._accssible_data

    def __len__(self):
        return len(self._accssible_data)

    def __iter__(self):
        return iter(self._accssible_data)

    def __contains__(self, key):
        return key in self._accssible_data

    def __repr__(self):
        return f"{type(self).__name__}"

    def __str__(self):
        return self.__repr__()
