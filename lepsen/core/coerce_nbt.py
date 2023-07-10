__all__ = [
    "NbtCoerceable",
    "coerce_nbt_value",
]


from collections.abc import Iterable, Mapping
from typing import Union

from nbtlib import (
    Base,
    Int,
    Byte,
    Double,
    String,
    Compound,
    List,
    Array,
)


NbtCoerceable = Union[
    Base,
    int,
    float,
    str,
    bool,
    Iterable["NbtCoerceable"],
    Mapping[str, "NbtCoerceable"],
]


def coerce_nbt_value(
    value: NbtCoerceable,
    *,
    deep_copy: bool = False,
) -> Base:
    """
    Convert a value into a serializable NBT tag and return it.

    Arguments:
    value -- the value to convert into the returned NBT tag

    Keyword Arguments:
    deep_copy (= False) -- when true, `value` will be left untouched and the
                           return value will not contain any references to
                           mutable data structures contained in `value`
    """
    is_base = isinstance(value, Base)
    is_mapping = isinstance(value, Mapping)
    is_nbt_container = is_base and isinstance(
        value,
        (Compound, List[List], List[Compound]),
    )
    is_nbt_scalar = is_base and not (
        is_nbt_container or
        isinstance(value, (List, Array))
    )
    if is_nbt_scalar:
        pass
    elif is_base and not deep_copy:
        if is_nbt_container:
            for k, v in value.items() if is_mapping else enumerate(value):
                value[k] = coerce_nbt_value(v)
    elif isinstance(value, bool):
        value = Byte(value)
    elif isinstance(value, int):
        value = Int(value)
    elif isinstance(value, float):
        value = Double(value)
    elif isinstance(value, str):
        value = String(value)
    elif is_mapping:
        value = Compound(
            (k, coerce_nbt_value(v, deep_copy=deep_copy)) for k, v in value.items()
        )
    elif is_nbt_container:
        value = type(value)([
            coerce_nbt_value(v, deep_copy=True) for v in value
        ])
    elif is_base:
        value = type(value)(value)
    elif isinstance(value, Iterable):
        value = List([
            coerce_nbt_value(v, deep_copy=True) for v in value
        ])
    else:
        raise TypeError(f"{value!r} cannot be converted to an NBT tag")
    return value
