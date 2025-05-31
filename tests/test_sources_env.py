import platform
from os import environ

import pytest

from byoconfig.error import BYOConfigError

from fixtures.fixture_source_classes import GenericEnvSource


def test_error_modes():
    with pytest.raises(BYOConfigError) as exec_info_error:
        GenericEnvSource(111)
    assert "env_prefix must be a string" in str(exec_info_error.value)

    with pytest.raises(BYOConfigError) as exec_info_error:
        GenericEnvSource(env_prefix="illegal prefix")
    assert " must be a valid environment variable name" in str(exec_info_error.value)


def load_env():
    environ.update(
        {
            "BYO_CONFIG_TEST2_VAR1": "value1",
            "BYO_CONFIG_TEST2_VAR2": "value2",
            "BYO_CONFIG_TEST2_var3": "value3",  # The case should be ignored on windows, converted to uppercase
        }
    )


def test_load_env():
    prefix = "BYO_CONFIG_TEST2_"
    load_env()
    env_source_1 = GenericEnvSource(prefix)
    # Test that it accepts either _ or no _ at the end of the prefix
    env_source_2 = GenericEnvSource(prefix[:-1])
    env_data = {
        "VAR1": "value1",
        "VAR2": "value2",
        "var3": "value3",
    }
    # Handle windows env var case insensitivity
    if platform.system() == "Windows":
        del env_data["var3"]
        env_data["VAR3"] = "value3"

    assert env_source_1.data == env_data
    assert env_source_2.data == env_data

    # Use the wildcard to load all environment variables
    env_source_3 = GenericEnvSource("*")
    # Due to slight difference between the two dictionaries, we will compare a subset of values
    if platform.system() == "Windows":
        assert env_source_3.data["HOMEDRIVE"] == environ.get("HOMEDRIVE")
        assert env_source_3.data["HOMEPATH"] == environ.get("HOMEPATH")
    else:
        assert env_source_3.data["HOME"] == environ.get("HOME")
        assert env_source_3.data["USER"] == environ.get("USER")

    # Test if using None as the prefix does not result in errors
    env_source_4 = GenericEnvSource(None)
    assert env_source_4.data == {}
