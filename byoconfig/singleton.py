import threading
from typing import Callable, Any

from byoconfig.config import Config

_singleton_lock = threading.Lock()


def singleton__new__method(_kls) -> Callable[..., Any]:
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with _singleton_lock:
                if cls._instance is None:
                    cls._instance = super(_kls, cls).__new__(cls)
        return cls._instance

    return __new__


class SingletonConfig(Config):
    _instance = None

    def __init_subclass__(cls, **kwargs):
        cls._instance = None
        cls.__new__ = singleton__new__method(SingletonConfig)
        super(SingletonConfig, cls).__init_subclass__(**kwargs)


class SingletonMetaclass(type):
    def __call__(cls, *args, **kwargs):
        with _singleton_lock:
            if not hasattr(cls, "_instance"):
                cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
