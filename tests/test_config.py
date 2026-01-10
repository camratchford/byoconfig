import datetime
import pathlib
import tempfile
from os import environ
from pathlib import Path
from json import loads as json_load
from mocks.mock_secrets_manager_client import MockSecretsManagerClient
from unittest.mock import patch

from yaml import safe_load as yaml_load
from toml import load as toml_load

from byoconfig.config import Config

from fixtures.pathing import example_configs, fixtures_dir
from fixtures.fixture_source_classes import (
    PluginVarSource,
    ASubClassOfSingletonConfig,
    new_instance_of_singleton,
)
from fixtures.secrets_manager_data import a_test_secret_data, a_test_secret


def test_base_variable_source_methods():
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
    example_dict = {"parent": {"some": "thing", "child": {"other": "thing"}}}

    yaml_file = str(example_configs / "same_as.yaml")
    yaml_source = Config(file_path=yaml_file)
    assert sorted(yaml_source.as_dict()) == sorted(example_dict)

    toml_file = str(example_configs / "same_as.toml")
    toml_source = Config(file_path=toml_file)
    assert sorted(toml_source.as_dict()) == sorted(example_dict)

    json_file = str(example_configs / "same_as.json")
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


def test_env_var_source_methods():
    """
    Test loading and dumping configuration data with environment variables.
    Note: Setting environment variables always results in a string.
    There isn't a good way to get the config data's original type, so we will only test string values.
    """

    # Test loading from env
    test_dict_1 = {"test_var_1": "abc", "test_var_2": "123"}

    environ.update(test_dict_1)

    env_config_1 = Config(env_prefix="test")
    assert env_config_1.get("var_1") == environ.get("test_var_1")
    assert env_config_1.get("var_2") == environ.get("test_var_2")

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


def test_singleton_config():
    """
    Any subsequent calls to SingletonConfig.__new__ should return the same instance
    """

    config1 = ASubClassOfSingletonConfig()
    config1.set("var1", 1)
    assert config1.get("var1")

    # Initialize the same class outside of this scope, it was supplied the init kwarg of var2=2
    config2 = new_instance_of_singleton()
    # Config2 should get the var1 variable
    assert config1.get("var1") == config2.get("var1") == 1
    # Config1 should have the var2 variable because config2 got it during __init__
    assert config1.get("var2") == config2.get("var2") == 2
    # They should both get the var3 variable, as it's part of ASubClassOfSingletonConfig's __init__ method
    assert config1.get("var3") == config2.get("var3") == 3
    # Overriding the var3 variable, making sure the change propagates
    config3 = ASubClassOfSingletonConfig(var3=4)
    assert config1.get("var3") == config2.get("var3") == config3.get("var3") == 4
    # Overriding it via .set instead of __init__'s kwargs
    config1.set("var3", 3)
    assert config1.get("var3") == config2.get("var3") == config3.get("var3") == 3


def test_type_conversion_loading():
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

    yaml_file = str(fixtures_dir / "types.yml")
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
    test_dict = {
        "test_date": datetime.date.today(),
        "test_datetime": datetime.datetime.now(),
        "test_path": pathlib.Path("./test"),
        "test_file": pathlib.Path("~/test"),
        "test_dir": pathlib.Path("/test"),
        "test_files": [
            pathlib.Path("test1"),
            pathlib.Path("test2"),
            pathlib.Path("test3"),
        ],
        "test_nested": {
            "another_test_dir": pathlib.Path("/test"),
        },
    }

    yaml_config = Config(**test_dict)
    toml_config = Config(**test_dict)
    json_config = Config(**test_dict)

    with tempfile.TemporaryDirectory() as tempdir:
        yaml_outfile = Path(tempdir) / "outfile.yml"
        yaml_config.dump_to_file(yaml_outfile)
        yaml_data = yaml_load(yaml_outfile.read_text())
        assert sorted(yaml_config.as_dict()) == sorted(yaml_data)

        toml_outfile = Path(tempdir) / "outfile.toml"
        toml_config.dump_to_file(toml_outfile)
        with open(toml_outfile) as f:
            toml_data = toml_load(f)
        assert sorted(toml_config.as_dict()) == sorted(toml_data)

        json_outfile = Path(tempdir) / "outfile.json"
        json_config.dump_to_file(json_outfile)
        json_data = json_load(json_outfile.read_text())
        assert sorted(json_config.as_dict()) == sorted(json_data)

        assert (
            sorted(test_dict.items())
            == sorted(yaml_data.items())
            == sorted(toml_data.items())
            == sorted(json_data.items())
        )


def test_tuple_and_set_conversion():
    # Ensure that values with the type set or tuple are implicitly converted to type list
    # necessary for mutual compatibility between YAML, TOML, JSON
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
            yaml_config_2.get("should_be_a_list")
            == yaml_data_2.get("should_be_a_list")
            == toml_config_2.get("should_be_a_list")
            == toml_data_2.get("should_be_a_list")
            == json_config_2.get("should_be_a_list")
            == json_data_2.get("should_be_a_list")
            == result_dict.get("should_be_a_list")
        )

        assert (
            yaml_config_2.get("should_also_be_a_list")
            == yaml_data_2.get("should_also_be_a_list")
            == toml_config_2.get("should_also_be_a_list")
            == toml_data_2.get("should_also_be_a_list")
            == json_config_2.get("should_also_be_a_list")
            == json_data_2.get("should_also_be_a_list")
            == result_dict.get("should_also_be_a_list")
        )
