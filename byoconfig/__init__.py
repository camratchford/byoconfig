from importlib.metadata import PackageNotFoundError, version

from .config import BYOConfig
from .singleton import SingletonMetaclass

try:
    __version__ = version("byoconfig")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["BYOConfig", "SingletonMetaclass", "__version__"]
