import logging
from typing import Callable, Literal, Optional, Any, Union
import datetime
import pathlib
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
from byoconfig.sources.type_conversion import (
    get_date_from_date_str,
    get_datetime_from_datetime_str,
    get_path_from_path_str,
    get_path_str_from_path,
    get_datetime_str_from_datetime,
    get_date_str_from_datetime,
    get_path_list_from_path_str_list,
)


logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml", ".toml"}
FileTypes = Optional[Literal["JSON", "YAML", "TOML"]]


class FileVariableSource(BaseVariableSource):
    """
    A VariableSource that loads data from a file.
    """

    _file_types: set[str] = {"JSON", "YAML", "TOML"}
    _file_method_types: set[str] = {"load", "dump"}
    _metadata: set[str] = BaseVariableSource._metadata.union(
        {
            "_file_types",
            "_file_method_types",
            "_valid_implied_types",
            "_key_suffix_to_type_loader_func",
            "_type_to_type_dumper_func",
        }
    )

    def __init__(self, **kwargs):
        super().__init__()
        self._key_suffix_to_type_loader_func = {
            "_path": get_path_from_path_str,
            "_file": get_path_from_path_str,
            "_dir": get_path_from_path_str,
            "_paths": get_path_list_from_path_str_list,
            "_files": get_path_list_from_path_str_list,
            "_dirs": get_path_list_from_path_str_list,
            "_date": get_date_from_date_str,
            "_datetime": get_datetime_from_datetime_str,
        }
        self._type_to_type_dumper_func = {
            datetime.date: get_date_str_from_datetime,
            datetime.datetime: get_datetime_str_from_datetime,
            pathlib.Path: get_path_str_from_path,
            # Blindly cast into a list, JSON and TOML don't support tuples or sets
            tuple: self.convert_dumped_configuration_data,
            set: self.convert_dumped_configuration_data,
            # Recurse
            list: self.convert_dumped_configuration_data,
            dict: self.convert_dumped_configuration_data,
        }

    def load_from_file(self, path: str = None, forced_type: FileTypes = None):
        if not path:
            return
        try:
            path = pathlib.Path(path)
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

            self.update(**configuration_data)

        except Exception as e:
            raise BYOConfigError(e.args[0], self)

    def dump_to_file(
        self, destination_path: pathlib.Path, forced_type: FileTypes = None
    ):
        destination_path = pathlib.Path(destination_path)
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
        source_file: pathlib.Path, forced_file_type: FileTypes = None
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
    ) -> Callable[[pathlib.Path], dict]:
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

    def _load_json(self, source_file: pathlib.Path) -> dict[Any, Any]:
        try:
            file_contents = source_file.read_text()
            data = json_load(file_contents)
            return self.convert_loaded_data(data)

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

    def _dump_json(self, destination_file: pathlib.Path):
        try:
            with open(destination_file, "w", encoding="utf-8") as json_file:
                out_data = self.convert_dumped_configuration_data(self._data)
                json = json_dump(out_data, indent=4)
                json_file.write(json)
        except Exception as e:
            raise BYOConfigError(
                f"Encountered an unhandled exception while dumping JSON file '{str(destination_file)}': {e.args}",
                self,
            ) from e

    def _load_yaml(self, source_file: pathlib.Path) -> dict[Any, Any]:
        try:
            with open(source_file, "r") as file:
                data = yaml_load(file)
                return self.convert_loaded_data(data)

        except MarkedYAMLError as e:
            raise BYOConfigError(
                f"Encountered YAML Error while decoding YAML file '{str(source_file)}': {e.args}",
                self,
            ) from e

    # Alias for load_yaml so the extension .yml can be used
    _load_yml = _load_yaml

    def _dump_yaml(self, destination_file: pathlib.Path):
        with open(destination_file, "w", encoding="utf-8") as yaml_file:
            try:
                out_data = self.convert_dumped_configuration_data(self._data)
                yaml_dump(out_data, yaml_file)

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

    def _load_toml(self, source_file: pathlib.Path) -> dict[Any, Any]:
        try:
            with open(source_file, "r") as file:
                data = toml_load(file)
                return self.convert_loaded_data(data)

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

    def _dump_toml(self, destination_file: pathlib.Path):
        try:
            with open(destination_file, "w", encoding="utf-8") as toml_file:
                out_data = self.convert_dumped_configuration_data(self._data)
                toml = toml_dump(out_data)
                toml_file.write(toml)

        except Exception as e:
            raise BYOConfigError(
                f"Encountered unhandled exception while dumping TOML file '{str(destination_file)}': {e.args}",
                self,
            ) from e

    def convert_loaded_configuration_value(self, key: str, value: Any):
        for suffix, converter in self._key_suffix_to_type_loader_func.items():
            if key.endswith(suffix):
                try:
                    return converter(value)
                except (ValueError, TypeError) as e:
                    raise BYOConfigError(
                        f"Could not convert '{key}' using {converter.__name__}: {e}",
                        self,
                    )
        return value

    def convert_loaded_data(self, data: dict[str, Any]) -> dict[str, Any]:
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = self.convert_loaded_data(value)
            else:
                data[key] = self.convert_loaded_configuration_value(key, value)
        return data

    def convert_dumped_configuration_value(self, value: Any):
        for _type, converter in self._type_to_type_dumper_func.items():
            if isinstance(value, _type):
                return converter(value)
        return value

    def convert_dumped_configuration_data(
        self, data: Union[dict[str, Any], list[Any], set[Any], tuple[Any]]
    ) -> Union[dict[str, Any], list[Any]]:
        if data == self._data:
            for key, value in data.items():
                data[key] = self.convert_dumped_configuration_value(value)
            return data
        if isinstance(data, list) or isinstance(data, set) or isinstance(data, tuple):
            data_copy = [self.convert_dumped_configuration_value(i) for i in data]
            return data_copy
        else:
            for key, value in data.items():
                data[key] = self.convert_dumped_configuration_value(value)
        return data
