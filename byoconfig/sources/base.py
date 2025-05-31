import logging

from copy import copy
from typing import Type

from byoconfig.error import BYOConfigError
from collections.abc import Hashable

logger = logging.getLogger(__name__)


class BaseVariableSource:
    """
    The base for other variable source object.
      - Provides methods to load, retrieve, and merge data from different sources.
      - Provides comparison methods to sort instances by precedence.

    Attrs:
        var_source_name (str):
            The name of the variable source. Must be unique for each instance.

        precedence (int):
            The precedence of the variable source.
            Higher precedence objects overwrite lower precedence objects when merged.

        metadata:
            Attributes to be ignored when exporting data from the instance.
            When creating a subclass of BaseVariableSource, add any attributes that
              should not be exported to this set.
    """

    _var_source_name: str = ""
    _precedence: int = 0
    _metadata = {"var_source_name", "precedence", "metadata"}

    def _clean_data(self, instance) -> dict:
        """
        Returns the data from the instance without the metadata attributes in dictionary form.
        Args:
            instance (object):
                The instance to extract data from
        """

        # noinspection PyTypeChecker
        if not isinstance(instance, BaseVariableSource):
            raise AttributeError(
                f"Unable to parse data from object {instance} as it "
                f"is not an instance or subclass instance of {self}"
            )

        return {
            k: v
            for k, v in instance.__dict__.items()
            if not k.startswith("_") and k not in self._metadata
        }

    def get_data(self):
        """
        Returns the data from the instance without the metadata attributes in dictionary form.
        """
        return self._clean_data(self)

    def set_data(self, data: dict = None, **kwargs):
        """
        Updates the object's attributes with the data from the source.
        Attributes do not need to be declared in the class definition.

        args:
            data (dict):
                The key:value pairs to be loaded as class atttributes
            **kwargs:
                Arbitrary keyword arguments, to be loaded as class attributes.
        """

        values = data or kwargs or None

        if values is None:
            return

        for attr, val in values.items():
            setattr(self, attr, val)

    @property
    def data(self):
        """
        Alias for get_data()
        Returns the data from the instance without the metadata attributes in dictionary form.
        """
        return self.get_data()

    @data.setter
    def data(self, data: dict):
        """
        Alias for set_data()
        Updates the object's attributes with the data from the source.
        Attributes do not need to be declared in the class definition.

        args:
            data (dict):
                The key:value pairs to be loaded as class atttributes
        """
        self.set_data(data)

    def clear_data(self, *args):
        """
        Clears the data from the instance.
        args:
            *args (list[hashable]):
                A list of keys to clear from the instance. If None, all keys will be cleared.
        """
        if args and not all([isinstance(a, Hashable) for a in args]):
            raise BYOConfigError(
                f"Unable to clear data from object {self} as one or more of the keys are not hashable types.",
                self,
            )

        keys = args if args else self.__dict__.keys()

        del_attrs = [
            k for k in keys if k not in self._metadata and k in self.__dict__.keys()
        ]

        for attr in del_attrs:
            delattr(self, attr)

    def __repr__(self):
        """
        Returns a string representation of the instance.
        """
        return (
            f"{self.__class__.__name__}: {self._var_source_name} [{self._precedence}]"
        )

    def __str__(self):
        """
        Returns a string representation of the instance.
        """
        return self.__repr__()

    def __int__(self):
        """
        Returns the precedence of the instance when cast to an integer.
        """
        return self._precedence

    def __hash__(self):
        """
        Returns the hash of the instance, based on precedence value
        """
        return hash(self._precedence)

    # 'Rich Comparison' magic methods to enable sorting by precedence
    def __lt__(self, other):
        """
        Returns true if the precedence of the right-hand object is greater than the precedence of the left-hand object.
        """
        return self._precedence < other._precedence

    def __le__(self, other):
        """
        Returns true if the precedence of the right-hand object is greater than or equal to the precedence of the left-hand object.
        """
        return self._precedence <= other._precedence

    def __gt__(self, other):
        """
        Returns true if the precedence of the right-hand object is less than the precedence of the left-hand object.
        """
        return self._precedence > other._precedence

    def __ge__(self, other):
        """
        Returns true if the precedence of the right-hand object is less than or equal to the precedence of the left-hand object.
        """
        return self._precedence >= other._precedence

    def __eq__(self, other):
        """
        Returns true if the precedence of the right-hand object is equal to the precedence of the left-hand object.
        """
        return hash(self) == hash(other)

    def __ne__(self, other):
        """
        Returns true if the precedence of the right-hand object is not equal to the precedence of the left-hand object.
        """
        return hash(self) != hash(other)

    def __add__(self, other: Type["BaseVariableSource"]):
        """
        Merges two instances together, with the instance with the higher precedence instance values overwriting
        the values of the lower precedence instance.
        """
        if other._precedence is None or self._precedence is None:
            raise BYOConfigError(
                f"Unable to merge object '{other}' with '{self}' as one or both instances have no precedence value.",
                self,
            )

        if not isinstance(other, self.__class__):
            raise BYOConfigError(
                f"Unable to merge object '{other}' with '{self}' as they are not instances of the same class.",
                self,
            )

        if self._var_source_name == other._var_source_name:
            raise BYOConfigError(
                f"Unable to merge object '{other}' with '{self}' as they share the same name.",
                self,
            )

        if self == other:
            raise BYOConfigError(
                f"Unable to merge object '{other}' with '{self}' as they have the same precedence.",
                self,
            )

        if self > other:
            data = self.get_data()
            other_data = self._clean_data(other)
            other_data.update(data)
            self.set_data(other_data)
            return copy(self)

        elif self < other:
            data = self._clean_data(self)
            other_data = self._clean_data(other)
            data.update(other_data)
            self.set_data(data)
            return copy(self)
