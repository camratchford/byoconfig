import threading
from typing import Callable, Any

from byoconfig.config import Config

_singleton_lock = threading.Lock()


def singleton__new__method() -> Callable[..., Any]:
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with _singleton_lock:
                # Double-check pattern
                if cls._instance is None:
                    cls._instance = object.__new__(cls)
        return cls._instance

    return __new__


class SingletonConfig(Config):
    _instance = None

    def __init_subclass__(cls, **kwargs):
        cls._instance = None
        cls.__new__ = singleton__new__method()
        super().__init_subclass__(**kwargs)
