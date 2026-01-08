import logging
from typing import Callable, Literal, Optional, Any
from pathlib import Path
from json import loads as json_load
from json import dumps as json_dump
from json.decoder import JSONDecodeError

from yaml import safe_load as yaml_load
from yaml import dump as yaml_dump
from yaml.error import MarkedYAMLError
from toml import load as toml_load
from toml import dumps as toml_dump
from toml.decoder import TomlDecodeError

from byoconfig.error import BYOConfigError
from byoconfig.sources.base import BaseVariableSource


logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml", ".toml"}
FileTypes = Optional[Literal["JSON", "YAML", "TOML"]]


class FileVariableSource(BaseVariableSource):
    """
    A VariableSource that loads data from a file.
    """

    _file_types = {"JSON", "YAML", "TOML"}
    _file_method_types = {"load", "dump"}

    _metadata: set[str] = BaseVariableSource._metadata.union(
        {"_file_types", "_file_method_types"}
    )

    def load_from_file(self, path: str = None, forced_type: FileTypes = None):
        if not path:
            return
        try:
            path = Path(path)
        except Exception as e:
            raise BYOConfigError(
                f"An exception occurred while loading file '{str(path)}': {e.args}",
                self,
            )
        if not path.exists():
            raise FileNotFoundError(f"Config file {str(path)} does not exist")

        try:
            extension = self._determine_file_type(path, forced_type)
            method = self._map_extension_to_load_method(extension, method_type="load")
            configuration_data = method(path)

            logger.debug(f"Read configuration data from '{str(path)}' as '{extension}'")

            self.update(configuration_data)

        except Exception as e:
            raise BYOConfigError(e.args[0], self)

    def dump_to_file(self, destination_path: Path, forced_type: FileTypes = None):
        destination_path = Path(destination_path)
        if not destination_path.parent.exists():
            destination_path.mkdir(mode=0o755, parents=True)

        file_type = self._determine_file_type(destination_path, forced_type)
        method = self._map_extension_to_load_method(file_type, method_type="dump")

        try:
            method(destination_path)
            logger.debug(
                f"Dumped configuration data to '{destination_path}' as '{file_type}'"
            )

        except Exception as e:
            raise BYOConfigError(
                f"Failed to dump file {destination_path} with type {file_type}: {e.args}",
                self,
            )

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
            if forced_file_type not in ALLOWED_EXTENSIONS:
                raise ValueError(
                    f"Forced file type '{forced_file_type}' is not one of the allowed file extensions: "
                    f"{str(ALLOWED_EXTENSIONS)}"
                )
            extension = f".{forced_file_type}"

        file_type: FileTypes = extension.lstrip(".").upper()  # type: ignore
        logger.debug(f"Determined file '{str(source_file)}' to be type '{file_type}'")

        return file_type

    def _map_extension_to_load_method(
        self, file_type: FileTypes, method_type: Literal["load", "dump"]
    ) -> Callable[[Path], dict]:
        """
        Maps the file typed (JSON, YAML, or TOML) to the appropriate load or dump method.
        """
        method_name = f"_{method_type}_{file_type.lower()}"

        if not hasattr(self, method_name):
            raise BYOConfigError(
                f"No FileVariableSource method exists for file type: '.{file_type.lower()}' "
                f"with operation {method_type}",
                self,
            )

        return getattr(self, method_name)

    def _load_json(self, source_file: Path) -> dict[Any, Any]:
        try:
            file_contents = source_file.read_text()
            data = json_load(file_contents)
            return data

        except UnicodeDecodeError as e:
            raise BYOConfigError(
                f"Encountered Unicode error while decoding file '{str(source_file)}': {e.args}",
                self,
            ) from e

        except JSONDecodeError as e:
            raise BYOConfigError(
                f"Encountered JSON error while decoding file '{str(source_file)}': {e.args}",
                self,
            ) from e

    def _dump_json(self, destination_file: Path):
        try:
            with open(destination_file, "w", encoding="utf-8") as json_file:
                json = json_dump(self._data, indent=4)
                json_file.write(json)
        except Exception as e:
            raise BYOConfigError(
                f"Encountered an unhandled exception while dumping JSON file '{str(destination_file)}': {e.args}",
                self,
            ) from e

    def _load_yaml(self, source_file: Path) -> dict[Any, Any]:
        try:
            with open(source_file, "r") as file:
                data = yaml_load(file)
                return data

        except MarkedYAMLError as e:
            raise BYOConfigError(
                f"Encountered YAML Error while decoding YAML file '{str(source_file)}': {e.args}",
                self,
            ) from e

    # Alias for load_yaml so the extension .yml can be used
    _load_yml = _load_yaml

    def _dump_yaml(self, destination_file: Path):
        with open(destination_file, "w", encoding="utf-8") as yaml_file:
            try:
                yaml_dump(self._data, yaml_file)

            except MarkedYAMLError as e:
                raise BYOConfigError(
                    f"Encountered YAML error while dumping YAML file {str(destination_file)}: {e.args}",
                    self,
                ) from e

            except Exception as e:
                raise BYOConfigError(
                    f"Encountered unhandled exception while dumping YAML file '{str(destination_file)}': {e}",
                    self,
                ) from e

    # Alias for dump_yaml so the extension .yml can be used
    _dump_yml = _dump_yaml

    def _load_toml(self, source_file: Path) -> dict[Any, Any]:
        try:
            with open(source_file, "r") as file:
                data = toml_load(file)
                return data

        except TomlDecodeError as e:
            raise BYOConfigError(
                f"Encountered TOML decode error while loading TOML file '{str(source_file)}': {e.args}",
                self,
            ) from e

        except Exception as e:
            raise BYOConfigError(
                f"Encountered unhandled exception while loading TOML file '{str(source_file)}': {e.args}",
                self,
            ) from e

    def _dump_toml(self, destination_file: Path):
        try:
            with open(destination_file, "w", encoding="utf-8") as toml_file:
                toml = toml_dump(self._data)
                toml_file.write(toml)

        except Exception as e:
            raise BYOConfigError(
                f"Encountered unhandled exception while dumping TOML file '{str(destination_file)}': {e.args}",
                self,
            ) from e
