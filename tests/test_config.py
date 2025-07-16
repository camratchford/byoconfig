from os import environ
from fixtures.pathing import example_configs
from fixtures.fixture_source_classes import PluginVarSource

import pytest

from byoconfig.config import Config


def test_file_var_source_functionality():
    example_dict = {"parent": {"some": "thing", "child": {"other": "thing"}}}

    yaml_file = str(example_configs / "same_as.yaml")
    yaml_source = Config(yaml_file)
    assert yaml_source.data == example_dict

    toml_file = str(example_configs / "same_as.toml")
    toml_source = Config(toml_file)
    assert toml_source.data == example_dict

    json_file = str(example_configs / "same_as.json")
    json_source = Config(json_file)
    assert json_source.data == example_dict


def test_env_var_source_functionality():
    env_prefix = "BYO_CONFIG_TEST_"
    env_var = "BYO_CONFIG_TEST_ENV_VAR"
    env_val = "test_value"

    env_dict = {env_var: env_val}
    environ.update(env_dict)

    env_source = Config(env_prefix=env_prefix)
    assert env_source.data.get("ENV_VAR") == environ.get(env_var)


def test_setattr_functionality():
    config_loose = Config(loose_attrs=True)
    a_nonexistent_attribute_var = config_loose.a_nonexistent_attribute
    assert a_nonexistent_attribute_var is None
    config_loose.another_nonexistent_attribute = 42
    assert config_loose.another_nonexistent_attribute == 42

    config_strict = Config()
    with pytest.raises(AttributeError):
        assert config_strict.a_nonexistent_attribute_var is None
        config_strict.another_nonexistent_attribute = 42
        assert config_strict.another_nonexistent_attribute == 42



def test_loading_plugins_and_kwargs():
    config = Config(
        precedence=0,
        test_var1="will_be_overwritten",
        test_var2="will_be_overwritten",
        test_var3="unique to config",
    )
    kwarg_str = "proof that we can pass plugins kwargs"
    config.include(PluginVarSource, plugin_kwarg=kwarg_str)
    assert config.data["test_var1"] == "from plugin #1"
    assert config.data["test_var2"] == "from plugin #2"
    assert config.data["test_var3"] == "unique to config"
    assert config.data["plugin_kwarg"] == kwarg_str
