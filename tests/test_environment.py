import os
from unittest import mock

import pytest

from byoconfig.sources import environment
from byoconfig.sources.environment import EnvVariableSource


class ExampleEnvSource(EnvVariableSource):
    host: str = "localhost"
    port: str = "80"


@pytest.fixture(autouse=True)
def isolated_environment():
    with mock.patch.dict(os.environ, clear=True):
        yield


@pytest.fixture
def source():
    return ExampleEnvSource()


def test_load_with_prefix_trims_prefix(source):
    os.environ["APP_HOST"] = "example.com"
    os.environ["APP_PORT"] = "443"

    source.load_from_environment(prefix="APP")

    assert source.get("host") == "example.com"
    assert source.get("port") == "443"


def test_load_without_trim_keeps_prefix():
    class PrefixedSource(EnvVariableSource):
        app_host: str = "localhost"

    source = PrefixedSource()
    os.environ["APP_HOST"] = "example.com"

    source.load_from_environment(prefix="APP", trim_prefix=False)

    assert source.get("app_host") == "example.com"


def test_load_with_prefix_skips_undeclared_keys(source):
    os.environ["APP_HOST"] = "example.com"
    os.environ["APP_UNKNOWN"] = "value"

    source.load_from_environment(prefix="APP")

    assert source.get("host") == "example.com"
    assert "unknown" not in source


def test_load_with_prefix_ignores_other_variables(source):
    os.environ["OTHER_HOST"] = "example.com"

    source.load_from_environment(prefix="APP")

    assert source.get("host") == "localhost"


def test_load_all_variables(source):
    os.environ["HOST"] = "example.com"
    os.environ["UNKNOWN"] = "value"

    source.load_from_environment(prefix="*")

    assert source.get("host") == "example.com"
    assert "unknown" not in source


@pytest.mark.parametrize("prefix", [None, ""])
def test_load_without_prefix_does_nothing(source, prefix):
    os.environ["HOST"] = "example.com"

    source.load_from_environment(prefix=prefix)

    assert source.get("host") == "localhost"


def test_load_uppercases_prefix_on_windows(source, monkeypatch):
    monkeypatch.setattr(environment.platform, "system", lambda: "Windows")
    os.environ["APP_HOST"] = "example.com"

    source.load_from_environment(prefix="app")

    assert source.get("host") == "example.com"


def test_load_non_string_prefix_raises_type_error(source):
    with pytest.raises(TypeError):
        source.load_from_environment(prefix=5)


def test_load_invalid_prefix_raises_value_error(source):
    with pytest.raises(ValueError):
        source.load_from_environment(prefix="1APP")


def test_dump_uses_uppercase_names(source):
    source.dump_to_environment()

    assert os.environ["HOST"] == "localhost"
    assert os.environ["PORT"] == "80"


def test_dump_with_prefix(source):
    source.dump_to_environment(with_prefix="app")

    assert os.environ["APP_HOST"] == "localhost"
    assert os.environ["APP_PORT"] == "80"


def test_dump_with_prefix_ending_in_underscore(source):
    source.dump_to_environment(with_prefix="APP_")

    assert os.environ["APP_HOST"] == "localhost"


def test_dump_keeps_case(source):
    source.dump_to_environment(use_uppercase=False, with_prefix="app")

    assert os.environ["app_host"] == "localhost"


def test_dump_selected_keys(source):
    source.dump_to_environment(selected_keys=["host"])

    assert os.environ["HOST"] == "localhost"
    assert "PORT" not in os.environ


def test_dump_converts_values_to_strings():
    class NumericSource(EnvVariableSource):
        port: int = 80

    NumericSource().dump_to_environment()

    assert os.environ["PORT"] == "80"


def test_dump_non_string_selected_key_raises_type_error(source):
    with pytest.raises(TypeError):
        source.dump_to_environment(selected_keys=["host", 5])


def test_dump_undefined_selected_key_raises_key_error(source):
    with pytest.raises(KeyError):
        source.dump_to_environment(selected_keys=["missing"])


def test_dump_invalid_prefix_raises_value_error(source):
    with pytest.raises(ValueError):
        source.dump_to_environment(with_prefix="1APP")


def test_dump_illegal_variable_name_raises_value_error(source):
    setattr(source, "bad=name", "value")

    with pytest.raises(ValueError, match="bad=name") as error_info:
        source.dump_to_environment(use_uppercase=False)

    assert isinstance(error_info.value.__cause__, ValueError)
