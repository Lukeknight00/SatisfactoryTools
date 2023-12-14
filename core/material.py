from dataclasses import fields, dataclass
from typing import Any
from numbers import Number
from functools import singledispatch


@dataclass
class MaterialSpec:
    # TODO: make this an attr accessible default dict, rather than dynamic dataclass

    @classmethod
    def empty(cls) -> MaterialSpec:
        return cls()

    def __lt__(self, other: Number) -> "MaterialSpec":
        """
        Return a MaterialSpec where values less than the given number are kept and remaining values set to
        their default.
        """

        return type(self)(
            **{name: value for (name, value) in self if value < other}
        )

    def __gt__(self, other: Number) -> "MaterialSpec":
        """
        Return a MaterialSpec where values greater than the given number are kept and remaining values set to
        their default.
        """

        return type(self)(
            **{name: value for (name, value) in self if value > other}
        )
    
    def __le__(self, other: Number) -> "MaterialSpec":
        """
        Return a MaterialSpec where values less than or equal to the given number are kept and remaining
        values set to their default.
        """

        return type(self)(
            **{name: value for (name, value) in self if value <= other}
        )

    def __ge__(self, other: Number) -> "MaterialSpec":
        """
        Return a MaterialSpec where values greater than or equal to the given number are kept and remaining
        values set to their default.
        """

        return type(self)(
            **{name: value for (name, value) in self if value >= other}
        )

    def __add__(self, other: "MaterialSpec" | Any) -> "MaterialSpec":
        if not isinstance(other, type(self)):
            return NotImplemented

        result = {}
        for name, value in self:
            result[name] = value + getattr(other, name)
        return type(self)(**result)

    def __sub__(self, other: "MaterialSpec" | Any) -> "MaterialSpec":
        if not isinstance(other, type(self)):
            return NotImplemented

        result = {}
        for name, value in self:
            result[name] = value - getattr(other, name)
        return type(self)(**result)

    def __mul__(self, scalar: Number) -> "MaterialSpec":
        result = {}
        for name, value in self:
            result[name] = value * scalar
        return type(self)(**result)

    @singledispatch
    def __truediv__(self, other: Any) -> Number | "MaterialSpec":
        return NotImplemented

    @__truediv__.register
    def _(self, other: Number) -> "MaterialSpec":
        result = {}
        for name, value in self:
            result[name] = value / other 

        return MaterialSpec(**result)

    @__truediv__.register
    def _(self, other: "MaterialSpec") -> Number:
        return min(getattr(self, name) / value for name, value in other if value > 0)

    @singledispatch
    def __div__(self, other: Any) -> int | "MaterialSpec":
        return NotImplemented

    @__div__.register
    def _(self, other: "MaterialSpec") -> int:
        return min(getattr(self, name) // value for name, value in other if value > 0)

    @__div__.register
    def _(self, other: Number) -> "MaterialSpec":
        result = {}
        for name, value in self:
            result[name] = value // other 
        return MaterialSpec(**result)

    def __iter__(self):
        for f in fields(self):
            yield f.name, getattr(self, f.name)

    def __or__(self, other: "MaterialSpec") -> "MaterialSpec":
        if not isinstance(other, MaterialSpec):
            return NotImplemented

        return type(self)(
            **{name: value for (name, value), (_, matched_value) in zip(self, other) if matched_value > 0})

    def __getitem__(self, item: str) -> Number:
        return getattr(self, item)

    def __repr__(self) -> str:
        return "\n".join(f"{name}: {value}" for name, value in self if value > 0)

