import logging
from typing import Callable, Literal, Optional, Any
from pathlib import Path
from json.decoder import JSONDecodeError
from json import loads as json_load
from json import dumps as json_dump

from yaml.error import MarkedYAMLError, YAMLError
from yaml import safe_load as yaml_load
from yaml import dump as yaml_dump
from toml.decoder import TomlDecodeError
from toml import load as toml_load
from toml import dumps as toml_dump

from byoconfig.error import BYOConfigError
from byoconfig.sources.base import BaseVariableSource


logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml", ".toml"}
FileTypes = Optional[Literal["JSON", "YAML", "TOML"]]


class FileVariableSource(BaseVariableSource):
    """
    A VariableSource that loads data from a file.
    """

    def __init__(
        self,
        source_file: Optional[str] = None,
        forced_file_type: FileTypes = None,
        **kwargs,
    ):
        """
        Initialize a FileVariableSource instance.

        Args:
            _var_source_name (str):
                The name of the variable source.

            _precedence (int):
                The precedence of the variable source.
                Higher precedence objects overwrite lower precedence objects when merged.

            source_file (str): The path to the source file.

            forced_file_type (FileTypes):
                The file type of the source file, if you don't want to use the file's extension.

            **kwargs:
                So that interface is consistent with other VariableSource classes.

        """
        if source_file is not None:
            source_file_path = Path(source_file)
            if not source_file_path.exists():
                raise FileNotFoundError(
                    f"Config file {str(source_file_path)} does not exist"
                )

            try:
                data = self._load_file(source_file_path, forced_file_type)
                self.set_data(data)
                logger.debug(f"Loaded data from file {str(source_file_path)}")

            except FileNotFoundError as e:
                raise e

            except JSONDecodeError as e:
                raise BYOConfigError(e.msg, self)

            except MarkedYAMLError as e:
                raise BYOConfigError(str(e), self)

            except YAMLError as e:
                raise BYOConfigError(str(e.args[0]), self)

            except TomlDecodeError as e:
                raise BYOConfigError(e.msg, self)

            except Exception as e:
                raise BYOConfigError(e.args[0], self)

    def load_file(self, source_file: Path, forced_file_type: FileTypes = None):
        """
        Loads the data from the source file.

        Args:
            source_file (Path):
                The path to the source file.

            forced_file_type (FileTypes):
                The file type of the source file, if you can't (or don't want to) use the file's extension.
        """
        self.set_data(self._load_file(source_file, forced_file_type))

    def _load_file(
        self, source_file: Path, forced_file_type: FileTypes = None
    ) -> dict[Any, Any]:
        """
        Loads the data from the source file.

        Args:
            source_file (Path):
                The path to the source file.

            forced_file_type (FileTypes):
                The file type of the source file, if you can't (or don't want to) use the file's extension.
        """

        if not source_file.exists():
            raise FileNotFoundError(f"Config file {str(source_file)} does not exist")

        try:
            extension = self._determine_file_type(source_file, forced_file_type)
            method = self._map_extension_to_load_method(extension, method_type="load")
            return method(source_file)

        except ValueError as e:
            logger.error(f"Error loading file {str(source_file)}")
            raise e

        except KeyError as e:
            logger.error(f"Error loading file {str(source_file)}")
            raise e

        except FileNotFoundError as e:
            logger.error(f"Error loading file {str(source_file)}")
            raise e

        except Exception as e:
            raise BYOConfigError(e.args[0], self)

    def dump(self, destination_path: Path, forced_file_type: FileTypes = None):
        """
        Dumps the data to a file.

        Args:
            destination_path (Path):
                The path to the destination file.

            forced_file_type (FileTypes):
                The file type of the source file, if you can't (or don't want to) use the file's extension.
        """
        destination_path = Path(destination_path)
        if not destination_path.parent.exists():
            destination_path.mkdir(mode=0o755, parents=True)

        file_type = self._determine_file_type(destination_path, forced_file_type)
        method = self._map_extension_to_load_method(file_type, method_type="dump")

        try:
            method(destination_path)

        except Exception as e:
            logger.error(f"Error dumping file {str(destination_path)}: {e}")
            raise e

    @staticmethod
    def _determine_file_type(
        source_file: Path, forced_file_type: FileTypes = None
    ) -> FileTypes:
        """
        Determines the file type of the source file. (One of 'JSON', 'YAML', 'TOML')
        """

        extension = source_file.suffix
        if not extension and not forced_file_type:
            raise ValueError(
                f"File provided [{str(source_file)}] has no file extension"
            )

        elif extension not in ALLOWED_EXTENSIONS and not forced_file_type:
            raise ValueError(
                f"File provided [{str(source_file)}] does not posses one of the allowed file extensions: "
                f"{str(ALLOWED_EXTENSIONS)}"
            )
        elif forced_file_type:
            extension = f".{forced_file_type}"

        file_type: FileTypes = extension.lstrip(".").upper()  # type: ignore
        return file_type

    def _map_extension_to_load_method(
        self, file_type: FileTypes, method_type: Literal["load", "dump"]
    ) -> Callable[[Path], dict]:
        """
        Maps the file extension to the appropriate load or dump method.

        Args:
            file_type (FileTypes):
                The file type of the source file. (One of 'JSON', 'YAML', 'TOML')

            method_type (Literal['load', 'dump']):
                The method type to map to.
        """

        method_name = f"_{method_type}_{file_type.lower()}"
        if not hasattr(self, method_name):
            raise ValueError(
                f"No FileVariableSource method exists for file type '.{file_type}'"
            )
        return getattr(self, method_name)

    @staticmethod
    def _load_json(source_file: Path) -> dict[Any, Any]:
        """
        Loads a JSON file.

        Args:
            source_file (Path):
                The path to the source file.
        """
        try:
            file_contents = source_file.read_text()
            data = json_load(file_contents)
            return data

        except UnicodeDecodeError as e:
            logger.error(f"Error decoding file {str(source_file)}: {e.args[0]}")
            raise e

        except JSONDecodeError as e:
            logger.error(f"Error decoding JSON file {str(source_file)}: {e.args[0]}")
            raise e

    def _dump_json(self, destination_file: Path):
        """
        Dumps the data to a JSON file.

        Args:
            destination_file (Path):
                The path to the destination file.
        """
        with open(destination_file, "w", encoding="utf-8") as json_file:
            json = json_dump(self.get_data(), indent=4)
            json_file.write(json)

    @staticmethod
    def _load_yaml(source_file: Path) -> dict[Any, Any]:
        """
        Loads a YAML file.

        Args:
            source_file (Path):
                The path to the source file.
        """
        try:
            with open(source_file, "r") as file:
                data = yaml_load(file)
                return data

        except MarkedYAMLError as e:
            logger.error(f"Error decoding YAML file {str(source_file)}: {e.args[0]}")
            raise e

    # Alias for load_yaml so the extension .yml can be used
    load_yml = _load_yaml

    def _dump_yaml(self, destination_file: Path):
        """
        Dumps the data to a YAML file.

        Args:
            destination_file (Path):
                The path to the destination file
        """
        with open(destination_file, "w", encoding="utf-8") as yaml_file:
            try:
                yaml_dump(self.get_data(), yaml_file)

            except MarkedYAMLError as e:
                logger.error(
                    f"Error dumping YAML file {str(destination_file)}: {e.args[0]}"
                )
                raise e

            except Exception as e:
                raise e

    # Alias for dump_yaml so the extension .yml can be used
    _dump_yml = _dump_yaml

    @staticmethod
    def _load_toml(source_file: Path) -> dict[Any, Any]:
        """
        Loads a TOML file.

        Args:
            source_file (Path):
                The path to the source file.
        """
        try:
            with open(source_file, "r") as file:
                data = toml_load(file)
                return data

        except TomlDecodeError as e:
            logger.error(f"Error decoding TOML file {str(source_file)}: {e.args[0]}")
            raise e

        except Exception as e:
            logger.error(f"Error decoding TOML file {str(source_file)}: {e.args[0]}")
            raise e

    def _dump_toml(self, destination_file: Path):
        """
        Dumps the data to a TOML file.

        Args:
            destination_file (Path):
                The path to the destination file.
        """
        with open(destination_file, "w", encoding="utf-8") as toml_file:
            toml = toml_dump(self.get_data())
            toml_file.write(toml)
