__all__ = [
    "CmdPrefix",
]


from typing import Optional, Union, Literal, overload
from collections.abc import Sequence, Iterator
from dataclasses import dataclass, field

from functools import partial
from math import log2


CMD_MAXIMUM = 2 ** 31
PRECISION_LOSS_START = 2 ** 24

internal_field = partial(field, init=False, compare=False, repr=False)


def float_precision_range(start: int, stop: Optional[int] = None, /) -> range:
    if start < 0:
        raise ValueError(
            "negative start breaks assumptions of internal helper function"
        )
    elif stop is not None and stop < start:
        raise ValueError(
            "stop < start breaks assumptions of internal helper function"
        )
    elif start < PRECISION_LOSS_START:
        step = 1
        max_stop = PRECISION_LOSS_START
    else:
        start_log2 = int(log2(start))
        step = 2 ** (start_log2 - 23)
        if rem := start % step:
            start += step - rem
        max_stop = 2 ** (start_log2 + 1)
    stop = max_stop if stop is None else min(stop, max_stop)
    return range(start, stop, step)


@dataclass(slots=True, frozen=True)
class CmdPrefix(Sequence[int]):
    """
    Helper class to generate valid, prefixed CustomModelData values.

    Indexing instances of this class will return correct values while automatically
    accounting for floating point precision loss for values above 2**24.
    """

    prefix: int
    multiplied_prefix: int = internal_field()
    precision_ranges: tuple["CmdPrefix.IndexPrecisionRange", ...] = internal_field()
    length: int = internal_field()

    def __post_init__(self, /):
        if self.prefix < 1 or self.prefix > 999:
            raise ValueError(
                f"Expected CustomModelData prefix in range [1, 999], got {self.prefix}",
            )
        def precision_range_iter() -> Iterator["CmdPrefix.IndexPrecisionRange"]:
            nonlocal self
            precision_range = self.IndexPrecisionRange(
                self.prefix, 0, self.prefix * 10_000
            )
            yield precision_range
            while precision_range.value_range.stop < CMD_MAXIMUM:
                precision_range = self.IndexPrecisionRange(
                    self.prefix,
                    precision_range.stop_index,
                    precision_range.value_range.stop,
                )
                yield precision_range
        precision_ranges = tuple(precision_range_iter())
        object.__setattr__(self, "precision_ranges", precision_ranges)
        object.__setattr__(self, "length", sum(
            len(r.index_range) for r in precision_ranges
        ))

    @overload
    def __getitem__(self, key: int, /) -> int:
        ...

    @overload
    def __getitem__(self, key: slice, /) -> "CmdPrefix.Slice":
        ...

    def __getitem__(self, key: Union[int, slice], /) -> Union[int, "CmdPrefix.Slice"]:
        if isinstance(key, slice):
            return self.Slice(self, key)
        key = range(0, self.length)[key]
        for precision_range in self.precision_ranges:
            if key in precision_range:
                return precision_range[key]
        raise IndexError("CustomModelData index out of range")

    def __len__(self, /) -> int:
        return self.length

    def __iter__(self, /) -> Iterator[int]:
        return iter(self.Slice(self, slice(None)))

    def __contains__(self, value: int, /) -> bool:
        return (
            value in range(0, CMD_MAXIMUM) and
            (value // 10_000) % 1_000 == self.prefix and
            float_precision_range(value).start == value
        )

    def count(self, value: int, /) -> Literal[0, 1]:
        return int(value in self)

    def index(self, value: int, /) -> int:
        if value not in self:
            raise ValueError(f"{value} not in {self!r}")
        for precision_range in self.precision_ranges:
            if value in precision_range.value_range:
                return precision_range.index(value)
        raise RuntimeError("unreachable code")

    @dataclass(frozen=True, slots=True, order=False)
    class Slice(Sequence[int]):
        target: "CmdPrefix"
        index_range: range
        _value_range: range = internal_field()

        @property
        def value_range(self, /) -> range:
            try:
                return self._value_range
            except AttributeError:
                start_index = self.index_range.start
                stop_index = self.index_range.stop
                min_index = min(start_index, stop_index)
                max_index = max(start_index, stop_index)
                if max_index < len(self.target):
                    highest_value = self.target[max_index]
                else:
                    highest_value = self.target[-1]
                    highest_value += float_precision_range(highest_value).step
                if max_index == min_index:
                    lowest_value = highest_value
                else:
                    lowest_value = self.target[min_index]
                if start_index < stop_index:
                    value_range = range(lowest_value, highest_value)
                else:
                    value_range = range(highest_value, lowest_value)
                object.__setattr__(self, "_value_range", value_range)
                return value_range

        def __init__(self, /, target: "CmdPrefix", slice: slice):
            index_range = range(0, len(target))[slice]
            object.__setattr__(self, "target", target)
            object.__setattr__(self, "index_range", index_range)

        @overload
        def __getitem__(self, key: int, /) -> int:
            ...

        @overload
        def __getitem__(self, key: range, /) -> "CmdPrefix.Slice":
            ...

        def __getitem__(
            self, key: Union[int, slice], /
        ) -> Union[int, "CmdPrefix.Slice"]:
            adjusted_key = self.index_range[key]
            if isinstance(adjusted_key, range):
                return CmdPrefix.Slice(self.target, slice(
                    adjusted_key.start,
                    None if adjusted_key.stop == -1 else adjusted_key.stop,
                    adjusted_key.step,
                ))
            else:
                return self.target[adjusted_key]

        def __len__(self, /) -> int:
            return len(self.index_range)

        def __iter__(self, /) -> Iterator[int]:
            return map(self.target.__getitem__, self.index_range)

        def __contains__(self, value: int, /) -> bool:
            return value in self.value_range and value in self.target

        def count(self, value: int, /) -> Literal[0, 1]:
            return int(value in self)

        def index(self, value: int, /) -> int:
            if value not in self:
                raise ValueError(f"{value} not in {self!r}")
            for precision_range in self.target.precision_ranges:
                if value in precision_range.value_range:
                    return precision_range.index(value)
                raise RuntimeError("unreachable code")

        def __repr__(self, /) -> str:
            start, stop, step = (
                self.index_range.start,
                self.index_range.stop,
                self.index_range.step,
            )
            if start == stop:
                start_str = str(start)
                stop_str = start_str
            elif step > 0:
                start_str = str(start) if start else ""
                stop_str = str(stop) if stop < len(self.target) else ""
            else:
                start_str = str(start) if start < len(self.target) - 1 else ""
                stop_str = str(stop) if stop >= 0 else ""
            step_str = f":{step}" if step != 1 else ""
            return f"{self.target!r}[{start_str}:{stop_str}{step_str}]"

    @dataclass(frozen=True, slots=True)
    class IndexPrecisionRange:
        prefix: int
        start_index: int
        stop_index: int = internal_field()
        value_range: range = internal_field()
        repetition_start_index: int = internal_field()
        repetition_period: int = internal_field()
        repetition_subdivision_length: int = internal_field()
        repetition_index_offsets: tuple[int, int] = internal_field()

        @property
        def index_range(self, /) -> range:
            return range(self.start_index, self.stop_index)

        def __init__(self, /, prefix: int, start_index: int, start_value: int):
            if start_value >= CMD_MAXIMUM:
                raise ValueError(
                    f"start value {start_value} being greater than or equal to "
                    f"{CMD_MAXIMUM} breaks assumptions of internal helper class"
                )
            elif start_index < 0:
                raise ValueError(
                    f"start index {start_index} being less than 0 breaks "
                    "assumptions of internal helper class"
                )
            value_precision_range = float_precision_range(start_value)
            adjusted_start = value_precision_range.start
            adjusted_full_prefix = adjusted_start // 10_000
            adjusted_base_prefix = adjusted_full_prefix % 1_000
            adjusted_extra_prefix = adjusted_full_prefix - adjusted_base_prefix
            stop_value = value_precision_range.stop
            step = value_precision_range.step
            if adjusted_base_prefix != prefix:
                if adjusted_base_prefix > prefix:
                    adjusted_extra_prefix += 1_000
                adjusted_full_prefix = adjusted_extra_prefix + prefix
                multiplied_full_prefix = adjusted_full_prefix * 10_000
                value_precision_range = float_precision_range(multiplied_full_prefix)
                if value_precision_range.step != step:
                    raise ValueError(
                        f"step changing from {step} to {value_precision_range.step} "
                        "breaks assumptions of internal helper class"
                    )
                adjusted_start = value_precision_range.start
                first_subdivision_start = adjusted_start
            else:
                multiplied_full_prefix = adjusted_full_prefix * 10_000
                first_subdivision_start = multiplied_full_prefix
                if rem := first_subdivision_start % step:
                    first_subdivision_start += step - rem
            value_range = range(
                adjusted_start - (start_index * step),
                stop_value,
                step,
            )
            first_subdivision = range(
                first_subdivision_start,
                min(multiplied_full_prefix + 10_000, stop_value),
                step,
            )
            second_subdivision_start = multiplied_full_prefix + 10_000_000
            if rem := second_subdivision_start % step:
                second_subdivision_start += step - rem
            if second_subdivision_start in value_range:
                second_subdivision = range(
                    second_subdivision_start,
                    min(multiplied_full_prefix + 10_010_000, stop_value),
                    step,
                )
            else:
                second_subdivision_start = first_subdivision.stop
                second_subdivision = range(
                    second_subdivision_start,
                    second_subdivision_start,
                    step,
                )
            repetition_start_index = value_range.index(first_subdivision_start)
            repetition_period = len(first_subdivision) + len(second_subdivision)
            first_to_second_offset = repetition_period if not second_subdivision else (
                value_range.index(second_subdivision_start) - repetition_start_index
            )
            if (first_subdivision_start + 20_000_000) not in value_range:
                repetition_index_offsets = (
                    first_to_second_offset,
                    first_to_second_offset + len(second_subdivision),
                )
                stop_index = repetition_start_index + repetition_period
            else:
                repetition_index_offsets = (
                    first_to_second_offset,
                    20_000_000 // step,
                )
                internal_stop_index = len(value_range) - repetition_start_index
                relative_stop_index = internal_stop_index % repetition_index_offsets[1]
                if relative_stop_index < first_to_second_offset:
                    relative_stop_index = min(
                        relative_stop_index,
                        len(first_subdivision),
                    )
                else:
                    relative_stop_index -= first_to_second_offset
                    relative_stop_index = min(
                        relative_stop_index + len(first_subdivision),
                        repetition_period,
                    )
                stop_index_repetitions = (
                    internal_stop_index // repetition_index_offsets[1]
                )
                stop_index = (
                    (stop_index_repetitions * repetition_period) +
                    relative_stop_index + repetition_start_index
                )
            for k, v in (
                ("prefix", prefix),
                ("start_index", start_index),
                ("stop_index", stop_index),
                ("value_range", value_range),
                ("repetition_start_index", repetition_start_index),
                ("repetition_period", repetition_period),
                ("repetition_subdivision_length", len(first_subdivision)),
                ("repetition_index_offsets", repetition_index_offsets),
            ):
                object.__setattr__(self, k, v)

        def __contains__(self, key: int, /) -> bool:
            return self.contains_key(key)

        def contains_key(self, key: int, /) -> bool:
            return key in self.index_range

        def contains_value(self, value: int, /) -> bool:
            try:
                return (self.value_range.index(value) >= self.start_index and
                        (value // 10_000) % 1_000 == self.prefix)
            except ValueError:
                return False

        def index(self, value: int, /) -> int:
            if not self.contains_value(value):
                raise ValueError(f"{value} is not in index precision range")
            internal_value_index = (
                self.value_range.index(value) - self.repetition_start_index
            )
            relative_value_index = (
                internal_value_index % self.repetition_index_offsets[1]
            )
            if relative_value_index > self.repetition_subdivision_length:
                relative_value_index -= self.repetition_index_offsets[0]
                relative_value_index += self.repetition_subdivision_length
            value_index_repetitions = (
                internal_value_index // self.repetition_index_offsets[1]
            )
            return (
                (value_index_repetitions * self.repetition_period) +
                relative_value_index + self.repetition_start_index
            )

        def __getitem__(self, key: int, /) -> int:
            if not self.contains_key(key):
                raise IndexError("index precision range index out of range")
            internal_index = key - self.repetition_start_index
            relative_index = internal_index % self.repetition_period
            if relative_index >= self.repetition_subdivision_length:
                relative_index -= self.repetition_subdivision_length
                relative_index += self.repetition_index_offsets[0]
            index_repetitions = internal_index // self.repetition_period
            return self.value_range[
                (index_repetitions * self.repetition_index_offsets[1]) +
                relative_index + self.repetition_start_index
            ]

        def __repr__(self, /) -> str:
            return (
                f"{type(self).__qualname__}("
                f"prefix={self.prefix}, "
                f"start_index={self.start_index}, "
                f"start_value={self.value_range[self.start_index]})"
            )
