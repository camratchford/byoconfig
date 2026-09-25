from typing import Annotated

import pytest

from byoconfig.sources.base import BaseVariableSource


class ExampleSource(BaseVariableSource):
    host: str = "localhost"
    port: int = 80
    token: Annotated[str, "excluded", "secret"] = "abc"
    region: Annotated[str, "secret"] = "us-east-1"
    _private: str = "hidden"

    def method(self):
        return "method"

    @property
    def computed(self):
        return "computed"

    @staticmethod
    def static_helper():
        return "static"


@pytest.fixture
def source():
    return ExampleSource()


def test_items_contain_only_public_data_attributes(source):
    assert dict(source.items()) == {
        "host": "localhost",
        "port": 80,
        "token": "abc",
        "region": "us-east-1",
    }


def test_instance_attribute_is_a_key(source):
    source.extra = "value"

    assert source.get("extra") == "value"
    assert "extra" in source


def test_instance_value_overrides_class_value(source):
    source.set("port", 8080)

    assert source.get("port") == 8080
    assert ExampleSource.port == 80


def test_get_returns_default_for_missing_key(source):
    assert source.get("missing", "fallback") == "fallback"


def test_set_unknown_key_raises_key_error(source):
    with pytest.raises(KeyError):
        source.set("missing", 1)


def test_set_private_key_raises_key_error(source):
    with pytest.raises(KeyError):
        source.set("_private", 1)


def test_update_with_mapping(source):
    source.update({"host": "example.com", "port": 443})

    assert source.get("host") == "example.com"
    assert source.get("port") == 443


def test_update_with_keyword_arguments(source):
    source.update(host="example.com")

    assert source.get("host") == "example.com"


def test_update_unknown_key_raises_key_error(source):
    with pytest.raises(KeyError):
        source.update({"missing": 1})


def test_update_skip_invalid_ignores_unknown_and_private_keys(source):
    source._update_skip_invalid({"host": "example.com", "missing": 1, "_private": 2})

    assert source.get("host") == "example.com"
    assert "missing" not in source
    assert source._private == "hidden"


def test_delete_overridden_key_reverts_to_class_default(source):
    source.set("port", 8080)
    source.delete_item("port")

    assert source.get("port") == 80


def test_delete_key_without_override_is_a_no_op(source):
    source.delete_item("port")

    assert source.get("port") == 80


def test_delete_instance_key_removes_it(source):
    source.extra = "value"
    source.delete_item("extra")

    assert "extra" not in source


def test_clear_data_reverts_all_keys(source):
    source.set("host", "example.com")
    source.set("port", 8080)
    source.extra = "value"

    source.clear_data()

    assert source.get("host") == "localhost"
    assert source.get("port") == 80
    assert "extra" not in source


def test_clear_data_with_selected_keys(source):
    source.set("host", "example.com")
    source.set("port", 8080)

    source.clear_data("host")

    assert source.get("host") == "localhost"
    assert source.get("port") == 8080


def test_get_by_prefix_trims_prefix(source):
    assert source.get_by_prefix("ho") == {"st": "localhost"}


def test_get_by_prefix_keeps_prefix(source):
    assert source.get_by_prefix("ho", trim_prefix=False) == {"host": "localhost"}


def test_get_by_annotated_type_matches_any(source):
    assert source.get_by_annotated_type("excluded", "secret") == {
        "token": "abc",
        "region": "us-east-1",
    }


def test_get_by_annotated_type_matches_all(source):
    assert source.get_by_annotated_type("excluded", "secret", all_must_match=True) == {
        "token": "abc"
    }


def test_get_by_annotated_type_without_matches(source):
    assert source.get_by_annotated_type("unused") == {}


def test_mapping_helpers(source):
    assert len(source) == 4
    assert list(source) == ["host", "port", "token", "region"]
    assert list(source.keys()) == ["host", "port", "token", "region"]
    assert list(source.values()) == ["localhost", 80, "abc", "us-east-1"]
    assert source.as_dict() == dict(source.items())


def test_inherited_class_attributes_are_not_keys():
    class ParentSource(BaseVariableSource):
        inherited: str = "parent"

    class ChildSource(ParentSource):
        own: str = "child"

    source = ChildSource()
    source._update_skip_invalid({"inherited": "changed", "own": "changed"})

    assert dict(source.items()) == {"own": "changed"}
    with pytest.raises(KeyError):
        source.set("inherited", "changed")
