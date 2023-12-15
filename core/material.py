from dataclasses import fields, dataclass
from typing import Any, Union
from numbers import Number
from functools import singledispatchmethod
from typing_extensions import Self


class _SignalClass:
    """
    Used for single dispatch on Self type
    """

@dataclass(frozen=True)
class MaterialSpec(_SignalClass):
    # TODO: make this an attr accessible default dict, rather than dynamic dataclass

    @classmethod
    def empty(cls) -> Self:
        return cls()

    def __lt__(self, other: Number) -> Self:
        """
        Return a MaterialSpec where values less than the given number are kept and remaining values set to
        their default.
        """

        return type(self)(
            **{name: value for (name, value) in self if value < other}
        )

    def __gt__(self, other: Number) -> Self:
        """
        Return a MaterialSpec where values greater than the given number are kept and remaining values set to
        their default.
        """

        return type(self)(
            **{name: value for (name, value) in self if value > other}
        )

    def __le__(self, other: Number) -> Self:
        """
        Return a MaterialSpec where values less than or equal to the given number are kept and remaining
        values set to their default.
        """

        return type(self)(
            **{name: value for (name, value) in self if value <= other}
        )

    def __ge__(self, other: Number) -> Self:
        """
        Return a MaterialSpec where values greater than or equal to the given number are kept and remaining
        values set to their default.
        """

        return type(self)(
            **{name: value for (name, value) in self if value >= other}
        )

    def __add__(self, other: Self | Any) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented

        result = {}
        for name, value in self:
            result[name] = value + getattr(other, name)
        return type(self)(**result)

    def __sub__(self, other: Self | Any) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented

        result = {}
        for name, value in self:
            result[name] = value - getattr(other, name)
        return type(self)(**result)

    def __mul__(self, scalar: Number) -> Self:
        result = {}
        for name, value in self:
            result[name] = value * scalar
        return type(self)(**result)

    @singledispatchmethod
    def __truediv__(self, other: Any) -> Number | Self:
        return NotImplemented

    @__truediv__.register
    def _(self, other: Number) -> Self:
        result = {}
        for name, value in self:
            result[name] = value / other 

        return type(self)(**result)

    @__truediv__.register(_SignalClass)
    def _(self, other: Self) -> Number:
        return min(getattr(self, name) / value for name, value in other if value > 0)

    @singledispatchmethod
    def __floordiv__(self, other: Any) -> int | Self:
        return NotImplemented

    @__floordiv__.register(_SignalClass)
    def _(self, other: Self) -> int:
        return min(getattr(self, name) // value for name, value in other if value > 0)

    @__floordiv__.register
    def _(self, other: Number) -> Self:
        result = {}
        for name, value in self:
            result[name] = value // other 
        return type(self)(**result)

    def __iter__(self):
        for f in fields(self):
            yield f.name, getattr(self, f.name)

    def __or__(self, other: Self) -> Self:
        if not isinstance(other, MaterialSpec):
            return NotImplemented

        return type(self)(
            **{name: value for (name, value), (_, matched_value) in zip(self, other) if matched_value > 0})

    def __getitem__(self, item: str) -> Number:
        return getattr(self, item)

    def __repr__(self) -> str:
        return "\n".join(f"{name}: {value}" for name, value in self if value > 0)

