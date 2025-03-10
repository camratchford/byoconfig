import pytest

from byoconfig.error import BYOConfigError

from fixtures.fixture_source_classes import GenericFileSource
from fixtures.pathing import example_configs, fixtures_dir, output_dir


def test_error_modes():
    # Test that the error modes are working as expected
    with pytest.raises(FileNotFoundError) as exec_info_file_not_found:
        GenericFileSource("non_existent_file", forced_file_type=None)
    assert "Config file non_existent_file does not exist" in str(
        exec_info_file_not_found.value
    )

    python_file = str(fixtures_dir / "fixture_source_classes.py")
    with pytest.raises(BYOConfigError) as exec_info_error:
        GenericFileSource(python_file, forced_file_type=None)
    assert "does not posses one of the allowed file extensions" in str(
        exec_info_error.value
    )

    invalid_json = str(fixtures_dir / "invalid.json")
    with pytest.raises(BYOConfigError) as exec_info_error:
        GenericFileSource(invalid_json, forced_file_type=None)
    assert "Expecting property name enclosed in double quotes " in str(
        exec_info_error.value
    )

    invalid_toml = str(fixtures_dir / "invalid.toml")
    with pytest.raises(BYOConfigError) as exec_info_error:
        GenericFileSource(invalid_toml, forced_file_type=None)
    assert "Invalid group name '{this is invalid}'." in str(exec_info_error.value)

    invalid_yaml = str(fixtures_dir / "invalid.yaml")
    with pytest.raises(BYOConfigError) as exec_info_error:
        GenericFileSource(invalid_yaml, forced_file_type=None)
    # todo: figure out how to get yaml error message


def test_load_file_modes():
    example_dict = {"parent": {"some": "thing", "child": {"other": "thing"}}}

    yaml_file = str(example_configs / "same_as.yaml")
    yaml_source = GenericFileSource(yaml_file)
    assert yaml_source.data == example_dict

    toml_file = str(example_configs / "same_as.toml")
    toml_source = GenericFileSource(toml_file)
    assert toml_source.data == example_dict

    json_file = str(example_configs / "same_as.json")
    json_source = GenericFileSource(json_file)
    assert json_source.data == example_dict


def compare_file_contents(file1, file2):
    with open(file1, "r") as f1:
        with open(file2, "r") as f2:
            return f1.read() == f2.read()


def test_dump_file_modes():
    # ensure that output_dir exists
    output_dir.mkdir(exist_ok=True)
    yaml_file = str(example_configs / "same_as.yaml")
    yaml_dump = str(output_dir / "dumped.yaml")
    yaml_source = GenericFileSource(yaml_file)
    yaml_source.dump(yaml_dump)
    assert compare_file_contents(yaml_file, yaml_dump)

    toml_file = str(example_configs / "same_as.toml")
    toml_dump = str(output_dir / "dumped.toml")
    toml_source = GenericFileSource(toml_file)
    toml_source.dump(toml_dump)
    assert compare_file_contents(toml_file, toml_dump)

    json_file = str(example_configs / "same_as.json")
    json_dump = str(output_dir / "dumped.json")
    json_source = GenericFileSource(json_file)
    json_source.dump(json_dump)
    assert compare_file_contents(json_file, json_dump)


def test_forced_file_type():
    yaml_file = str(fixtures_dir / "this_is_yaml")
    yaml_source = GenericFileSource(yaml_file, forced_file_type="YAML")
    assert yaml_source.data == {"this": "is yaml"}

    toml_file = str(fixtures_dir / "this_is_toml")
    toml_source = GenericFileSource(toml_file, forced_file_type="TOML")
    assert toml_source.data == {"parent": {"this": "is toml"}}

    json_file = str(fixtures_dir / "this_is_json")
    json_source = GenericFileSource(json_file, forced_file_type="JSON")
    assert json_source.data == {"this": "is json"}
