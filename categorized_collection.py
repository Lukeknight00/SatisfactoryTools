from collections import defaultdict
from typing import ParamSpec, Generic

T = ParamSpec("T")
S = ParamSpec("S")


class CategorizedCollection(Generic[T, S]):
    """
    Class  that stores a dictionary and categories for each of its items. This allows
    access to items directly, as well as by category.
    """
    _values: dict
    _tags: dict
    _inverse_tags: dict

    def __init__(self, items: dict[T, S] = None, tags: dict[str, set[T]] = None):
        self._tags = defaultdict(set)
        self._inverse_tags = defaultdict(set)
        if tags is not None:
            self._tags.update(tags)
            for tag, values in tags.items():
                for v in values:
                    self._inverse_tags[v].add(tag)

        self._values = items or {}

    def keys(self):
        yield from self._values.keys()

    def items(self):
        yield from self._values.items()

    def values(self):
        yield from self._values.values()

    def update(self, other: "Self"):
        self._values.update(dict(other.items()))

        for tag, values in other.tags.items():
            for v in values:
                self.set_tag(v, tag)

    def set_tag(self, item, tag):
        self._tags[tag].add(item)
        self._inverse_tags[item].add(tag)

    def __getitem__(self, item):
        return self._values[item]

    def __setitem__(self, key, value):
        self._values[key] = value

    def __contains__(self, item):
        return item in self._values

    @property
    def tags(self):
        return self._tags

    def value_tags(self, tag):
        return self._inverse_tags[tag]

    def tag(self, tag):
        value_keys = self._tags[tag]
        inverse_tags = {v: self._inverse_tags[v] for v in value_keys}
        tags_dict = defaultdict(set)
        for k, value_set in inverse_tags.items():
            for v in value_set:
                tags_dict[v].add(k)

        values_dict = {k: self._values[k] for k in value_keys}

        return type(self)(values_dict, tags_dict)
