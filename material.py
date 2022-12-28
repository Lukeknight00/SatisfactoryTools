from dataclasses import fields


class MaterialSpec:
    def __add__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        result = {}
        for name, value in self:
            result[name] = value + getattr(other, name)
        return type(self)(**result)

    def __sub__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        result = {}
        for name, value in self:
            result[name] = value - getattr(other, name)
        return type(self)(**result)

    def __mul__(self, scalar):
        result = {}
        for name, value in self:
            result[name] = value * scalar
        return type(self)(**result)

    def __iter__(self):
        for f in fields(self):
            yield f.name, getattr(self, f.name)

    def __or__(self, other):
        if isinstance(other, type(self)):
            return type(self)(
                **{name: value for (name, value), (_, matched_value) in zip(self, other) if matched_value > 0})
        # elif isinstance(other, Material):
        #     return type(self)(**{other.name: getattr(self, other.name)})
        elif isinstance(other, str):
            return type(self)(**{other: getattr(self, other)})

        return NotImplemented

    def __getitem__(self, item):
        return getattr(self, item)

    def __repr__(self):
        return "\n".join(f"{name}: {value}" for name, value in self if value > 0)
