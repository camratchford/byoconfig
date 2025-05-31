from byoconfig.config import Config


class SingletonConfig(Config):
    """
    Singleton class of the byoconfig.Config object:
        Once initialized, any subsequent calls to this class's __init__ method will return
        the original SingletonConfig object from the first time it was called.

    Useful for:
        An application with a single config context, allowing you to import and initialize
        a single instance across any scope while having access to a single instance of the
        Config class (and all the data within).

    Not useful for:
        Multiple config contexts that require separate instances of Config objects.
        If that is your goal, you should use Config or implement your own singleton class from
        the Config class, re-using this class's __new__ method, as subclassing this class
        will automatically overwrite the original singleton's __new__ method.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SingletonConfig, cls).__new__(cls, *args, **kwargs)
        return cls._instance
