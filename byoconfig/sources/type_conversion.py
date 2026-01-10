from datetime import date, datetime
from pathlib import Path
from typing import Any, Union
from re import compile, Pattern
from collections.abc import Mapping, Iterable, Reversible


supported_export_types: set[type] = {
    str,
    int,
    float,
    dict,
    list,
    tuple,
    set,
    date,
    datetime,
    Path,
}

# Group 1: Any path start token '/', '~/', or './'
# Group 2: Absolute path  '/'
# Group 3: Relative to HOME path '~/'
# Group 4: Relative to PWD path './'
# Group 5: Subpath relative to the start token.
path_regex: Pattern = compile(r"((^/)|(^~/)|(^./))(.*)")

valid_date_formats: set[str] = {
    "%Y-%m-%d",
}

default_datetime_format = "%Y-%m-%dT%H:%M:%S%z"
# Based on TOML
valid_datetime_formats: set[str] = {
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d",
    "%H:%M:%S.%f",
    "%H:%M:%S",
}


def is_mapping(obj: Any):
    return isinstance(obj, Mapping)


def collapse_mapping(mapping: Mapping[str, Any]):
    """
    Extracts unique last-generation child items
    """

    dicts = [([], mapping)]
    ret = {}
    seen = set()
    for path, d in dicts:
        if id(d) in seen:
            continue
        seen.add(id(d))
        for k, v in d.items():
            new_path = path + [k]
            if type(v) not in supported_export_types:
                raise ValueError(f"Value type '{type(v)}' is not an exportable type")
            if hasattr(v, "items"):
                dicts.append((new_path, v))
            else:
                ret[k] = v
    return ret


def is_iterable(obj: Any):
    return (
        isinstance(obj, Iterable)
        and isinstance(obj, Reversible)
        and not isinstance(obj, Mapping)
    )


def collapse_iterable(iterable: Union[Iterable, Reversible]):
    result = []
    stack = list(reversed(iterable))

    while stack:
        item = stack.pop()
        if type(item) not in supported_export_types:
            raise ValueError(f"Value type '{type(item)}' is not an exportable type")
        if is_iterable(item):
            stack.extend(reversed(item))
        else:
            result.append(item)

    return result


def get_date_from_date_str(maybe_date_str: str):
    try:
        return datetime.strptime(
            maybe_date_str,
            "%Y-%m-%d",
        )
    except ValueError:
        pass

    return None


def get_datetime_from_datetime_str(maybe_datetime_str: str):
    for fmt in valid_datetime_formats:
        try:
            return datetime.strptime(maybe_datetime_str, fmt)
        except ValueError:
            continue
    return None


def get_path_str_from_path(path: Path):
    path_str = path.as_posix()
    return path_str


def get_path_str_list_from_path_list(path_list: list[Path]):
    results_list = []
    if not path_list or not isinstance(path_list, list):
        return path_list

    for path in path_list:
        results_list.append(get_path_str_from_path(path))

    return results_list


def get_datetime_str_from_datetime(datetime_obj: datetime):
    return datetime_obj.strftime(format=default_datetime_format)


def get_date_str_from_datetime(datetime_obj: datetime):
    return datetime_obj.strftime(format="%Y-%m-%d")


def get_path_from_path_str(path_str: str):
    try:
        return Path(path_str)
    except (TypeError, ValueError):
        pass
    return path_str


def get_path_list_from_path_str_list(path_str_list: list[str]):
    results_list = []
    if not path_str_list or not isinstance(path_str_list, list):
        return path_str_list

    for path_str in path_str_list:
        results_list.append(get_path_from_path_str(path_str))

    return results_list
