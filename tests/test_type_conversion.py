from byoconfig.sources.type_conversion import collapse_mapping, collapse_iterable


def test_collapse_mapping():
    test_dict = {
        "abc": [1, 2, 3],
        "a": {"aa": {"aaa": 111}, "bb": {"bbb": 222}},
        "b": {"aa": {"ccc": 333}, "bb": {"ddd": 444}},
        "c": {"aa": {"ccc": 333}, "bb": {"ddd": 444}},
    }
    collapsed_dict = collapse_mapping(test_dict)
    assert list(collapsed_dict.keys()) == ["abc", "aaa", "bbb", "ccc", "ddd"]
    assert list(collapsed_dict.values()) == [[1, 2, 3], 111, 222, 333, 444]


def test_collapse_iterable_to_values():
    test_list = [1, [2, 3, 4], [[5, 6, 7], [8, 9, 10], [[11, 12, 13], [14, 15, 16]]]]
    assert collapse_iterable(test_list) == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
    ]
