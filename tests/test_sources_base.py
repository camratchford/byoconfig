import pytest

from fixtures.fixture_source_classes import NameSource
from byoconfig.error import BYOConfigError


def test_base_source():
    source = NameSource("test")
    assert source.data == {"name": "test", "should_appear": "should_appear"}
    assert source._var_source_name == "NameSource"
    assert source._precedence == 1
    assert str(source) == "NameSource: NameSource [1]"
    assert repr(source) == "NameSource: NameSource [1]"
    source_keys = [k for k in source.data.keys()]
    assert "precedence" not in source_keys
    assert "var_source_name" not in source_keys
    assert "metadata" not in source_keys
    assert "_should_not_appear" not in source_keys
    assert "should_appear" in source_keys


def test_precedence_and_add():
    source_a = NameSource("a", "source_a", 1)
    source_b = NameSource("b", "source_b", 2)
    source_c = NameSource("c", "source_c", 1)
    source_d = NameSource("d", "source_d", 2)

    # Test __add__ method
    source_a = source_a + source_b
    assert source_a.data == {"name": "b", "should_appear": "should_appear"}

    # Test all other magic methods that use precedence
    assert int(source_a) == 1
    assert source_a < source_b
    assert source_a <= source_b
    assert source_a <= source_c
    assert source_b > source_a
    assert source_b >= source_a
    assert source_b >= source_d
    assert source_a != source_b
    assert source_a == source_c

    with pytest.raises(BYOConfigError) as exec_info_precedence:
        source_a += source_c
        assert "as they have the same precedence." in str(exec_info_precedence.value)

    source_c.precedence = None
    with pytest.raises(BYOConfigError) as exec_info_no_precedence:
        source_a += source_c
        assert "as one or both instances have no precedence value." in str(
            exec_info_no_precedence.value
        )

    # Test that private attributes are not copied over
    source_b._should_not_appear = "shouldn't be copied to other source"
    source_a += source_b
    assert source_a.data == {"name": "b", "should_appear": "should_appear"}
    assert source_a._should_not_appear != source_b._should_not_appear


def test_name_conflict():
    source_a = NameSource("a", "source_a", 1)
    source_b = NameSource("b", "source_a", 2)
    with pytest.raises(BYOConfigError) as exec_info_name:
        source_a += source_b
    assert "as they share the same name." in str(exec_info_name.value)


def test_set_data():
    source_a = NameSource("a", "source_a", 1)
    source_a.data = {"name": "b"}
    assert source_a.data == {"name": "b", "should_appear": "should_appear"}

    # Source should be unchanged if data is set to None
    source_a.data = None
    assert source_a.data == {"name": "b", "should_appear": "should_appear"}

    # Source should be unchanged if data is set to an empty dict
    source_a.data = {}
    assert source_a.data == {"name": "b", "should_appear": "should_appear"}

    # Test clear_data method with no args
    source_a.clear_data()
    assert source_a.data == {}

    # Test clear_data method with args
    source_a.data = {"name": "b", "age": 30}
    source_a.clear_data("name", "should_appear")
    assert source_a.data == {"age": 30}

    # Test clear_data method with non-hashable args
    with pytest.raises(BYOConfigError) as exec_info:
        source_a.clear_data(["name"])
    assert "not hashable types." in str(exec_info.value)
