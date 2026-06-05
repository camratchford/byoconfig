import datetime
import pathlib
import tempfile
from json import loads as json_load
from os import environ
from pathlib import Path
from typing import Annotated
from unittest.mock import patch

import pytest
from fixtures.pathing import fixtures_dir
from fixtures.secrets_manager_data import a_test_secret, a_test_secret_data
from mocks.mock_secrets_manager_client import MockSecretsManagerClient
from toml import load as toml_load
from yaml import safe_load as yaml_load


def test_base_variable_source_methods():
    from byoconfig.config import Config

    config_no_attrs = Config(config_assign_attrs=False, test=1)
    assert not hasattr(config_no_attrs, "test")
    assert config_no_attrs.get("test") == 1

    config = Config(config_name="test-config", config_assign_attrs=True, test=1)
    assert config.name == "test-config"
    assert config.test == 1

    config.set("test_1", 1)
    assert config.test_1 == 1

    config.delete_item("test")
    assert not hasattr(config, "test")
    assert config.get("test", "missing") == "missing"

    # Ensure that the update method's data parameter works
    config.update({"test_2": 4})
    assert config.get("test_2") == 4

    # Ensure that the update method's kwargs parameter works
    config.update(test_2=2)
    assert config.get("test_2") == 2

    # Ensure that you can't provide both data and kwargs to the update method
    config.delete_item("test_2")
    config.update({"test_2": 2}, test_3=3)
    assert "test_2" not in config
    assert "test_3" in config

    # Test the get_by_prefix method
    config.update(not_test_prefix="Doesn't have the test_ prefix")
    assert "test_1" in config.get_by_prefix("test", trim_prefix=False)
    assert "test_prefix" in config.get_by_prefix("not", trim_prefix=True)

    # Test config.as_dict()
    config.clear_data()
    config.update(test_1=1, test_2=2)
    assert isinstance(config.as_dict(), dict)
    assert config.as_dict() == {
        "test_1": 1,
        "test_2": 2,
    }

    # Test config.keys and config.values
    config.update(test_3=3)
    assert "test_3" in config.keys()
    assert 3 in config.values()

    # Test config.__len__
    assert len(config) == 3


def test_file_var_source_methods():
    """
    Testing loading data and dumping data with YAML, TOML, and JSON.
    Note: We need to sort the dictionaries because each of the loaders load the data differently
    """
    from byoconfig.config import Config

    example_dict = {"parent": {"some": "thing", "child": {"other": "thing"}}}

    yaml_file = str(fixtures_dir / "same_as.yaml")
    yaml_source = Config(file_path=yaml_file)
    assert sorted(yaml_source.as_dict()) == sorted(example_dict)

    toml_file = str(fixtures_dir / "same_as.toml")
    toml_source = Config(file_path=toml_file)
    assert sorted(toml_source.as_dict()) == sorted(example_dict)

    json_file = str(fixtures_dir / "same_as.json")
    json_source = Config(file_path=json_file)
    assert sorted(json_source.as_dict()) == sorted(example_dict)

    # Test the dump methods against the contents of the input files
    with tempfile.TemporaryDirectory() as tempdir:
        yaml_outfile = Path(tempdir) / "outfile.yml"
        yaml_source.dump_to_file(yaml_outfile)
        yaml_data = yaml_load(yaml_outfile.read_text())
        assert sorted(yaml_source.as_dict()) == sorted(yaml_data)

        toml_outfile = Path(tempdir) / "outfile.toml"
        toml_source.dump_to_file(toml_outfile)
        with open(toml_outfile) as f:
            toml_data = toml_load(f)
        assert sorted(toml_source.as_dict()) == sorted(toml_data)

        json_outfile = Path(tempdir) / "outfile.json"
        json_source.dump_to_file(json_outfile)
        json_data = json_load(json_outfile.read_text())
        assert sorted(json_source.as_dict()) == sorted(json_data)

        assert (
            sorted(example_dict)
            == sorted(yaml_data)
            == sorted(toml_data)
            == sorted(json_data)
        )


def test_annotated_configs():
    from byoconfig.config import Config

    with tempfile.TemporaryDirectory() as tempdir:

        class AnnotatedConfig(Config):
            should_be_exported: str = "test1"
            should_not_be_exported: Annotated[str, "excluded"] = "test2"

        annotated_config = AnnotatedConfig()

        strings = annotated_config.get_by_annotated_type(str)
        excluded = annotated_config.get_by_annotated_type("excluded")
        assert strings
        assert excluded
        export_test_file = Path(tempdir) / "export_test.yml"
        annotated_config.dump_to_file(export_test_file)
        export_test_data = yaml_load(export_test_file.read_text())

        assert export_test_data.get("should_be_exported") == "test1"
        assert export_test_data.get("should_not_be_exported") is None


def test_env_var_source_methods():
    """
    Test loading and dumping configuration data with environment variables.
    Note: Setting environment variables always results in a string.
    There isn't a good way to get the config data's original type, so we will only test string values.
    """
    from byoconfig.config import Config

    # Test loading from env
    test_dict_1 = {"test_var_1": "abc", "test_var_2": "123"}
    test_dict_2 = {"TEST_VAR_3": "efg"}
    environ.update(test_dict_1)

    env_config_1 = Config(env_prefix="test")
    assert env_config_1.get("var_1") == environ.get("test_var_1")
    assert env_config_1.get("var_2") == environ.get("test_var_2")

    environ.update(test_dict_2)
    env_config_1.load_from_environment(prefix="TEST")
    assert env_config_1.get("var_3") == "efg"

    # Test the "*" special value for env_prefix
    env_config_2 = Config(env_prefix="*")

    assert env_config_2.get("PATH") == environ.get("PATH")

    # Test dumping to env
    test_dict_2 = {"foo": "xyz", "bar": "890"}
    env_config_2 = Config(**test_dict_2)

    env_config_2.dump_to_environment()
    assert environ.get("FOO") == "xyz" and environ.get("BAR") == "890"

    env_config_2.dump_to_environment(selected_keys=["foo"], use_uppercase=False)
    assert environ.get("foo") == "xyz"

    env_config_2.dump_to_environment(
        selected_keys=["foo"], use_uppercase=True, with_prefix="test"
    )
    assert environ.get("TEST_FOO") == "xyz"

    env_config_2.dump_to_environment(
        selected_keys=["foo", "bar"], use_uppercase=False, with_prefix="another_test"
    )
    assert (
        environ.get("another_test_foo") == "xyz"
        and environ.get("another_test_bar") == "890"
    )


def test_aws_secrets_manager_methods():
    from byoconfig.config import Config

    mock_client = MockSecretsManagerClient()
    secret_name = "a-test-secret"
    mock_client.add_secret(secret_id=secret_name, secret_string=a_test_secret)

    with patch(
        "byoconfig.sources.aws_secrets_manager.boto3.client", return_value=mock_client
    ):
        config = Config(aws_secret_name=secret_name)
        config.load_from_secrets_manager(aws_secret_name=secret_name)
        for k, v in a_test_secret_data.items():
            assert config.get(k) == v


def test_config_include_method():
    from fixtures.fixture_source_classes import PluginVarSource

    from byoconfig.config import Config

    config = Config(
        test_var1="will_be_overwritten",
        test_var2="will_be_overwritten",
        test_var3="unique to config",
    )
    kwarg_str = "proof that we can pass plugins kwargs"
    config.include(PluginVarSource, plugin_kwarg=kwarg_str)
    assert config.get("test_var1") == "from plugin #1"
    assert config.get("test_var2") == "from plugin #2"
    assert config.get("test_var3") == "unique to config"
    assert config.get("plugin_kwarg") == kwarg_str


def test_type_conversion_loading():
    from byoconfig.config import Config

    toml_file = str(fixtures_dir / "types.toml")
    toml_config = Config(file_path=toml_file)
    toml_data = toml_config.as_dict()
    assert isinstance(toml_data.get("ssh_private_key_file"), Path)
    assert isinstance(toml_data.get("date_1"), datetime.datetime)
    assert isinstance(toml_data.get("date_2"), datetime.datetime)
    assert isinstance(toml_data.get("date_3"), datetime.date)
    assert isinstance(toml_data.get("owner").get("dob"), datetime.datetime)
    assert isinstance(toml_data.get("file_locations").get("this_file"), Path)
    assert all(
        isinstance(v, Path)
        for v in toml_data.get("file_locations").get("a_list_of_paths")
    )

    yaml_file = str(fixtures_dir / "types.yaml")
    yaml_config = Config(file_path=yaml_file)
    yaml_data = yaml_config.as_dict()
    assert isinstance(yaml_data.get("ssh_private_key_file"), Path)
    assert isinstance(yaml_data.get("date_1"), datetime.datetime)
    assert isinstance(yaml_data.get("date_2"), datetime.datetime)
    assert isinstance(yaml_data.get("date_3"), datetime.date)
    assert isinstance(yaml_data.get("owner").get("dob"), datetime.datetime)
    assert isinstance(yaml_data.get("file_locations").get("this_file"), Path)
    assert all(
        isinstance(v, Path)
        for v in yaml_data.get("file_locations").get("a_list_of_paths")
    )

    json_file = str(fixtures_dir / "types.json")
    json_config = Config(file_path=json_file)
    json_data = json_config.as_dict()
    assert isinstance(json_data.get("ssh_private_key_file"), Path)
    assert isinstance(json_data.get("date_1"), datetime.datetime)
    assert isinstance(json_data.get("date_2"), datetime.datetime)
    assert isinstance(json_data.get("date_3"), datetime.date)
    assert isinstance(json_data.get("owner").get("dob"), datetime.datetime)
    assert isinstance(json_data.get("file_locations").get("this_file"), Path)
    assert all(
        isinstance(v, Path)
        for v in json_data.get("file_locations").get("a_list_of_paths")
    )


def test_type_conversion_dumping():
    # Ensure that datetime.date, datetime.datetime, and pathlib.Path
    # can be created from their string representations

    from byoconfig.config import Config

    class ConversionTestConfig(Config):
        test_none_dir: Path = None

    # We actually don't care about microseconds, so we'll trim them
    now = datetime.datetime.now()
    now = now.replace(microsecond=0)
    test_dict = {
        "test_date": datetime.date.today(),
        "test_datetime": now,
        "test_path": pathlib.Path("./test"),
        "test_file": pathlib.Path("~/test"),
        "test_dir": pathlib.Path("/test"),
        "test_none_dir": None,
        "test_files": [
            pathlib.Path("test1"),
            pathlib.Path("test2"),
            pathlib.Path("test3"),
        ],
        "test_nested": {
            "another_test_dir": pathlib.Path("/test"),
        },
    }

    yaml_config = ConversionTestConfig(**test_dict)
    toml_config = ConversionTestConfig(**test_dict)
    json_config = ConversionTestConfig(**test_dict)

    with tempfile.TemporaryDirectory() as tempdir:
        yaml_outfile = Path(tempdir) / "outfile.yml"
        yaml_config.dump_to_file(yaml_outfile)
        yaml_config_reloaded = ConversionTestConfig()
        yaml_config_reloaded.load_from_file(str(yaml_outfile))
        assert sorted(yaml_config.as_dict().items()) == sorted(
            yaml_config_reloaded.as_dict().items()
        )

        toml_outfile = Path(tempdir) / "outfile.toml"
        toml_config.dump_to_file(toml_outfile)
        toml_config_reloaded = ConversionTestConfig()
        toml_config_reloaded.load_from_file(str(toml_outfile))
        assert sorted(toml_config.as_dict().items()) == sorted(
            toml_config_reloaded.as_dict().items()
        )

        json_outfile = Path(tempdir) / "outfile.json"
        json_config.dump_to_file(json_outfile)
        json_config_reloaded = ConversionTestConfig()
        json_config_reloaded.load_from_file(str(json_outfile))
        assert sorted(json_config.as_dict().items()) == sorted(
            json_config_reloaded.as_dict().items()
        )

        assert (
            sorted(test_dict.items())
            == sorted(yaml_config_reloaded.as_dict().items())
            == sorted(toml_config_reloaded.as_dict().items())
            == sorted(json_config_reloaded.as_dict().items())
        )


def test_tuple_and_set_conversion():
    # Ensure that values with the type set or tuple are implicitly converted to type list
    # necessary for mutual compatibility between YAML, TOML, JSON

    from byoconfig.config import Config

    test_dict_2 = {
        "should_be_a_list": ("value_1", "value_2"),
        "should_also_be_a_list": {"value_1", "value_2"},
    }
    result_dict = {
        "should_be_a_list": ["value_1", "value_2"],
        "should_also_be_a_list": ["value_2", "value_1"],
    }

    yaml_config_2 = Config(**test_dict_2)
    toml_config_2 = Config(**test_dict_2)
    json_config_2 = Config(**test_dict_2)

    with tempfile.TemporaryDirectory() as tempdir:
        yaml_outfile_2 = Path(tempdir) / "outfile_2.yml"
        yaml_config_2.dump_to_file(yaml_outfile_2)
        yaml_data_2 = yaml_load(yaml_outfile_2.read_text())

        toml_outfile_2 = Path(tempdir) / "outfile_2.toml"
        toml_config_2.dump_to_file(toml_outfile_2)
        with open(toml_outfile_2) as f:
            toml_data_2 = toml_load(f)

        json_outfile_2 = Path(tempdir) / "outfile_2.json"
        json_config_2.dump_to_file(json_outfile_2)
        json_data_2 = json_load(json_outfile_2.read_text())

        assert isinstance(yaml_config_2.get("should_be_a_list"), list)
        assert isinstance(toml_config_2.get("should_be_a_list"), list)
        assert isinstance(json_config_2.get("should_be_a_list"), list)
        assert isinstance(yaml_config_2.get("should_also_be_a_list"), list)
        assert isinstance(toml_config_2.get("should_also_be_a_list"), list)
        assert isinstance(json_config_2.get("should_also_be_a_list"), list)

        assert (
            sorted(yaml_config_2.get("should_be_a_list"))
            == sorted(yaml_data_2.get("should_be_a_list"))
            == sorted(toml_config_2.get("should_be_a_list"))
            == sorted(toml_data_2.get("should_be_a_list"))
            == sorted(json_config_2.get("should_be_a_list"))
            == sorted(json_data_2.get("should_be_a_list"))
            == sorted(result_dict.get("should_be_a_list"))
        )

        assert (
            sorted(yaml_config_2.get("should_also_be_a_list"))
            == sorted(yaml_data_2.get("should_also_be_a_list"))
            == sorted(toml_config_2.get("should_also_be_a_list"))
            == sorted(toml_data_2.get("should_also_be_a_list"))
            == sorted(json_config_2.get("should_also_be_a_list"))
            == sorted(json_data_2.get("should_also_be_a_list"))
            == sorted(result_dict.get("should_also_be_a_list"))
        )


def test_class_attrs():
    from fixtures.fixture_source_classes import (
        ConfigWithClassAttrs,
    )

    config = ConfigWithClassAttrs(var_1=2)
    # Set in ConfigWithInstanceAttrs.__init__
    assert config.get("class_attr_1") == 1
    assert config.get("var_1") == 2


def test_instance_attrs():
    from fixtures.fixture_source_classes import (
        ConfigWithInstanceAttrs,
    )

    config = ConfigWithInstanceAttrs(var_1=2)

    # Set in ConfigWithInstanceAttrs.__init__
    assert config.get("instance_var_1") == 1
    assert config.get("var_1") == 2


def test_annotated_attrs():
    from byoconfig.config import Config

    class ConfigWithAnnotatedAttrs(Config):
        class_var_annotated: Annotated[str, "something"] = "should appear"
        class_var_naked: str = "shouldn't appear"

        # Shouldn't appear, as it does not match 'something'
        class_var_annotated_not_included: Annotated[str, "not_something"] = (
            "shouldn't appear"
        )

        # Works with types as well. Might use this later for type coercion.
        class_var_with_type: Annotated[str, int] = "123"

        # Will only appear if it gets a value later
        class_var_that_gets_value_later: Annotated[str, "something"]

        def __init__(self, **kwargs):
            self.class_var_that_gets_value_later = "should also appear"
            super().__init__(**kwargs)

    config = ConfigWithAnnotatedAttrs()

    assert config.get_by_annotated_type("something")
    assert config.get_by_annotated_type("something") == {
        "class_var_annotated": "should appear",
        "class_var_that_gets_value_later": "should also appear",
    }

    assert config.get_by_annotated_type(int)
    assert config.get_by_annotated_type(int) == {"class_var_with_type": "123"}


def test_dumping_excluded_attrs():
    from byoconfig.config import Config

    class ConfigThatDumpsAnnotatedAttrs(Config):
        class_var_excluded: Annotated[str, "excluded"] = "don't export me"
        class_var_naked: str = "export me"
        class_var_annotated_included: Annotated[str, "not_something"] = "export me"
        # If value is defined before `super().__init__()` is called, it doesn't need a value now
        class_var_that_gets_value_later_excluded: Annotated[str, "excluded"]
        class_var_that_gets_value_later_included: str
        # If value is defined within or after `super()__init__()` (file, env, aws, kwargs), a value must be defined now
        class_var_added_via_init_excluded: Annotated[str, "excluded"] = None
        class_var_added_via_init_included: str

        def __init__(self, **kwargs):
            self.class_var_that_gets_value_later_included = "export me"
            self.class_var_that_gets_value_later_excluded = "don't export me"
            super().__init__(**kwargs)

    with tempfile.TemporaryDirectory() as tempdir:
        out_file = Path(tempdir) / "dumped_config.yml"
        dumping_config = ConfigThatDumpsAnnotatedAttrs(
            class_var_added_via_init_excluded="123",
            class_var_added_via_init_included="abc",
        )
        dumping_config.dump_to_file(out_file)

        with open(out_file, "r") as yaml_out:
            dumped_config = yaml_load(yaml_out)
            assert "class_var_excluded" not in dumped_config
            assert "class_var_naked" in dumped_config
            assert "class_var_annotated_included" in dumped_config
            assert "class_var_that_gets_value_later_included" in dumped_config
            assert "class_var_that_gets_value_later_excluded" not in dumped_config
            assert "class_var_added_via_init_excluded" not in dumped_config
            assert "class_var_added_via_init_included" in dumped_config


def test_non_existent_file_path_arg():
    from byoconfig.config import Config

    # Exception not raised
    Config(file_path="a_path_that_doesnt_exist.yml", file_not_exists_ok=True)
    # Exception raised
    with pytest.raises(FileNotFoundError):
        # With default file_not_exists_ok=False
        Config(file_path="a_path_that_doesnt_exist.yml")
