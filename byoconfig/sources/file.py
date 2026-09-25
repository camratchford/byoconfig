import logging
from json import dumps as json_dump
from json import loads as json_load
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Optional

from toml import dumps as toml_dump
from toml import load as toml_load
from toml.decoder import TomlDecodeError
from yaml import safe_dump as yaml_dump
from yaml import safe_load as yaml_load
from yaml.error import MarkedYAMLError
from yaml.representer import RepresenterError

from byoconfig.sources.base import BaseVariableSource

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml", ".toml"}
FileTypes = Optional[Literal["JSON", "YAML", "TOML"]]


class FileVariableSource(BaseVariableSource):
    """
    A VariableSource that loads data from a file.
    """

    _file_types: set[str] = {"JSON", "YAML", "TOML"}
    _file_method_types: set[str] = {"load", "dump"}
    _file_prevent_export_annotations: set[str | type[Any]] = {"excluded"}
    """
    If the type annotation of a config key is typing.Annotated[self._prevent_export_annotations], 
    that key/value will not be exported when the self.dump_to_file method is run and will not appear 
    in self.exported_data.
    """

    def get_data_from_file(
        self,
        path: Path | str | None = None,
        forced_type: FileTypes = None,
        enforce_mapping_type: bool = False,
        not_exists_ok: bool = False,
    ):
        if path is None and not_exists_ok:
            return {}

        if not path:
            raise TypeError(
                f"Invalid path argument. Expected non-empty str or Path type — got {type(path)}"
            )

        path = Path(path)

        if not path.exists():
            if not_exists_ok:
                return {}

            raise FileNotFoundError(f"Config file {path.as_posix()} does not exist")

        extension = self._determine_file_type(path, forced_type)
        method = self._map_extension_to_load_method(extension, method_type="load")
        configuration_data = method(path)
        if enforce_mapping_type and not isinstance(configuration_data, Mapping):
            raise TypeError(
                f"Top-level data structure in {path.as_posix()} is not a Mapping "
                f"— got {type(configuration_data).__name__}"
            )

        logger.debug(f"Read configuration data from '{str(path)}' as '{extension}'")

        return configuration_data

    def load_from_file(
        self,
        path: Path | str | None = None,
        forced_type: FileTypes = None,
        enforce_mapping_type: bool = False,
        not_exists_ok: bool = False,
    ):
        data = self.get_data_from_file(
            path,
            forced_type,
            enforce_mapping_type,
            not_exists_ok,
        )
        self.update(**data)

    def dump_to_file(self, destination_path: Path, forced_type: FileTypes = None):
        destination_path = Path(destination_path)
        file_type = self._determine_file_type(destination_path, forced_type)
        serialize = self._map_extension_to_load_method(file_type, method_type="dump")
        file_contents = serialize()

        destination_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        destination_path.write_text(file_contents, encoding="utf-8")
        logger.debug(
            f"Dumped configuration data to '{destination_path}' as '{file_type}'"
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
            extension = f".{forced_file_type.lower()}"
            if extension not in ALLOWED_EXTENSIONS:
                raise ValueError(
                    f"Forced file type '{forced_file_type}' is not one of the allowed file types: "
                    f"{str(FileVariableSource._file_types)}"
                )

        file_type: FileTypes = extension.lstrip(".").upper()  # type: ignore
        logger.debug(f"Determined file '{str(source_file)}' to be type '{file_type}'")

        return file_type

    def _map_extension_to_load_method(
        self, file_type: FileTypes, method_type: Literal["load", "dump"]
    ) -> Callable[..., Any]:
        """
        Maps the file typed (JSON, YAML, or TOML) to the appropriate load or dump method.
        """
        method_name = f"_{method_type}_{file_type.lower()}"

        if not hasattr(self, method_name):
            raise ValueError(
                f"No FileVariableSource method exists for file type: '.{file_type.lower()}' "
                f"with operation {method_type}"
            )

        return getattr(self, method_name)

    def _load_json(self, source_file: Path) -> dict[Any, Any]:
        try:
            file_contents = source_file.read_text()
            if not file_contents.strip():
                return {}
            data = json_load(file_contents)
            if data:
                return data
            return {}

        except UnicodeDecodeError as e:
            raise ValueError(
                f"Encountered Unicode error while decoding file '{str(source_file)}': {e.args}"
            ) from e

        except JSONDecodeError as e:
            raise ValueError(
                f"Encountered JSON error while decoding file '{str(source_file)}': {e.args}"
            ) from e

    def _dump_json(self) -> str:
        return json_dump(self.exportable_data, indent=4)

    def _load_yaml(self, source_file: Path) -> dict[Any, Any]:
        try:
            with open(source_file, "r") as file:
                data = yaml_load(file)
                if data:
                    return data
                return {}

        except MarkedYAMLError as e:
            raise ValueError(
                f"Encountered YAML Error while decoding YAML file '{str(source_file)}': {e.args}"
            ) from e

    # Alias for load_yaml so the extension .yml can be used
    _load_yml = _load_yaml

    def _dump_yaml(self) -> str:
        try:
            return yaml_dump(self.exportable_data)

        except RepresenterError as e:
            raise TypeError(
                f"Encountered unrepresentable value while dumping YAML: {e.args}"
            ) from e

    # Alias for dump_yaml so the extension .yml can be used
    _dump_yml = _dump_yaml

    def _load_toml(self, source_file: Path) -> dict[Any, Any]:
        try:
            with open(source_file, "r") as file:
                data = toml_load(file)
                if data:
                    return data
                return {}

        except TomlDecodeError as e:
            raise ValueError(
                f"Encountered TOML decode error while loading TOML file '{str(source_file)}': {e.args}"
            ) from e

    def _dump_toml(self) -> str:
        return toml_dump(self.exportable_data)

    @property
    def exportable_data(self):
        return {
            name: value
            for name, value in self._accssible_data.items()
            if name not in self.get_by_annotated_type("excluded")
        }
