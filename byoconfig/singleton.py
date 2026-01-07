import threading
from typing import Dict, Type, Any, TypeVar
from functools import wraps

_instances: Dict[Type, Any] = {}
_lock = threading.Lock()

T = TypeVar('T')


def singleton_class(cls: Type[T]) -> Type[T]:
    """
    Create a thread-safe singleton from a regular class.
    """

    original_new = cls.__new__

    @wraps(original_new)
    def singleton_new(klass, *args, **kwargs):
        if cls not in _instances:
            with _lock:
                if cls not in _instances:
                    if original_new is object.__new__:
                        instance = object.__new__(klass)
                    else:
                        instance = original_new(klass, *args, **kwargs)
                    _instances[cls] = instance
        return _instances[cls]

    cls.__new__ = staticmethod(singleton_new)
    return cls
