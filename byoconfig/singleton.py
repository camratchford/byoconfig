import threading

_singleton_lock = threading.RLock()


class SingletonMetaclass(type):
    def __call__(cls, *args, **kwargs):
        with _singleton_lock:
            if "_instance" not in cls.__dict__:
                cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
