from json import JSONDecodeError
from typing import Annotated

import pytest
from toml.decoder import TomlDecodeError
from yaml.error import MarkedYAMLError

from byoconfig.sources.file import FileVariableSource


class ExampleFileSource(FileVariableSource):
    host: str = "localhost"
    port: int = 80
    password: Annotated[str, "excluded"] = "secret"


@pytest.fixture
def source():
    return ExampleFileSource()


@pytest.mark.parametrize("extension", ["json", "yaml", "yml", "toml"])
def test_dump_and_load_round_trip(source, tmp_path, extension):
    path = tmp_path / f"config.{extension}"
    source.set("host", "example.com")
    source.set("port", 443)

    source.dump_to_file(path)
    loaded_source = ExampleFileSource()
    loaded_source.load_from_file(path)

    assert loaded_source.get("host") == "example.com"
    assert loaded_source.get("port") == 443


@pytest.mark.parametrize("extension", ["json", "yaml", "toml"])
def test_dump_omits_excluded_keys(source, tmp_path, extension):
    path = tmp_path / f"config.{extension}"

    source.dump_to_file(path)

    assert "password" not in source.get_data_from_file(path)


def test_exportable_data_omits_excluded_keys(source):
    assert source.exportable_data == {"host": "localhost", "port": 80}


def test_dump_creates_missing_parent_directories(source, tmp_path):
    path = tmp_path / "nested" / "directory" / "config.json"

    source.dump_to_file(path)

    assert path.is_file()


@pytest.mark.parametrize(
    ("forced_type", "contents"),
    [
        ("JSON", '{"host": "example.com"}'),
        ("YAML", "host: example.com\n"),
        ("TOML", 'host = "example.com"\n'),
    ],
)
def test_load_with_forced_type(source, tmp_path, forced_type, contents):
    path = tmp_path / "config"
    path.write_text(contents)

    source.load_from_file(path, forced_type=forced_type)

    assert source.get("host") == "example.com"


def test_dump_with_forced_type(source, tmp_path):
    path = tmp_path / "config"

    source.dump_to_file(path, forced_type="TOML")

    assert source.get_data_from_file(path, forced_type="TOML") == {
        "host": "localhost",
        "port": 80,
    }


def test_invalid_forced_type_raises_value_error(source, tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{}")

    with pytest.raises(ValueError):
        source.load_from_file(path, forced_type="XML")


def test_missing_extension_raises_value_error(source, tmp_path):
    path = tmp_path / "config"
    path.write_text("{}")

    with pytest.raises(ValueError):
        source.load_from_file(path)


def test_unsupported_extension_raises_value_error(source, tmp_path):
    path = tmp_path / "config.txt"
    path.write_text("{}")

    with pytest.raises(ValueError):
        source.load_from_file(path)


def test_missing_file_raises_file_not_found_error(source, tmp_path):
    with pytest.raises(FileNotFoundError):
        source.load_from_file(tmp_path / "missing.json")


def test_missing_file_with_not_exists_ok_returns_empty(source, tmp_path):
    assert (
        source.get_data_from_file(tmp_path / "missing.json", not_exists_ok=True) == {}
    )


def test_no_path_with_not_exists_ok_returns_empty(source):
    assert source.get_data_from_file(None, not_exists_ok=True) == {}


@pytest.mark.parametrize("path", [None, ""])
def test_empty_path_raises_type_error(source, path):
    with pytest.raises(TypeError):
        source.get_data_from_file(path)


@pytest.mark.parametrize(
    ("extension", "contents", "cause"),
    [
        ("json", "{", JSONDecodeError),
        ("yaml", "host: [", MarkedYAMLError),
        ("toml", "host = ", TomlDecodeError),
    ],
)
def test_invalid_contents_raise_value_error(
    source, tmp_path, extension, contents, cause
):
    path = tmp_path / f"config.{extension}"
    path.write_text(contents)

    with pytest.raises(ValueError, match=str(path)) as error_info:
        source.load_from_file(path)

    assert isinstance(error_info.value.__cause__, cause)


def test_invalid_unicode_raises_value_error(source, tmp_path):
    path = tmp_path / "config.json"
    path.write_bytes(b"\xff\xfe\xfa")

    with pytest.raises(ValueError) as error_info:
        source.load_from_file(path)

    assert isinstance(error_info.value.__cause__, UnicodeDecodeError)


@pytest.mark.parametrize("extension", ["json", "yaml", "toml"])
def test_empty_file_loads_nothing(source, tmp_path, extension):
    path = tmp_path / f"config.{extension}"
    path.write_text("")

    assert source.get_data_from_file(path) == {}


def test_enforce_mapping_type_rejects_list(source, tmp_path):
    path = tmp_path / "config.json"
    path.write_text("[1, 2]")

    with pytest.raises(TypeError):
        source.load_from_file(path, enforce_mapping_type=True)


def test_load_unknown_key_raises_key_error(source, tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"missing": 1}')

    with pytest.raises(KeyError):
        source.load_from_file(path)


def test_failed_dump_does_not_create_file(source, tmp_path):
    path = tmp_path / "nested" / "config.json"
    source.set("host", object())

    with pytest.raises(TypeError):
        source.dump_to_file(path)

    assert not path.exists()
    assert not path.parent.exists()


def test_failed_dump_leaves_existing_file_unchanged(source, tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"host": "original"}')
    source.set("host", object())

    with pytest.raises(TypeError):
        source.dump_to_file(path)

    assert path.read_text() == '{"host": "original"}'


def test_unsupported_extension_dump_does_not_create_directory(source, tmp_path):
    path = tmp_path / "nested" / "config.txt"

    with pytest.raises(ValueError):
        source.dump_to_file(path)

    assert not path.parent.exists()


@pytest.mark.parametrize("extension", ["yaml", "yml"])
def test_unrepresentable_yaml_value_raises_type_error(source, tmp_path, extension):
    path = tmp_path / f"config.{extension}"
    source.set("host", object())

    with pytest.raises(TypeError):
        source.dump_to_file(path)

    assert not path.exists()


def test_yaml_dump_has_no_python_tags(source, tmp_path):
    path = tmp_path / "config.yaml"
    source.set("host", ("example.com", 443))

    source.dump_to_file(path)

    assert "!!python" not in path.read_text()
    assert source.get_data_from_file(path)["host"] == ["example.com", 443]
