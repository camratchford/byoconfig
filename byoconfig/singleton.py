import threading

_singleton_lock = threading.Lock()


class SingletonMetaclass(type):
    def __call__(cls, *args, **kwargs):
        with _singleton_lock:
            if not hasattr(cls, "_instance"):
                cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
