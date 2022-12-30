from collections import defaultdict
from typing import ParamSpec

T = ParamSpec("T")
S = ParamSpec("S")


class CategorizedCollection:
    """
    Class  that stores a dictionary and categories for each of its items. This allows
    access to items directly, as well as by category.
    """
    _values: dict
    _tags: dict

    def __init__(self, items: dict[T, S] = None, tags: dict[str, set[T]] = None):
        self.tags = defaultdict(list)
        if tags:
            self.tags.update(tags)

        self.items = items or {}

    def keys(self):
        yield from self._values.keys()

    def items(self):
        yield from self._values.items()

    def values(self):
        yield from self._values.values()

    def update(self, other: "Self"):
        self._values.update(dict(other.items))

        for tag in other.tags:
            self._tags[tag] = self.tags[tag] | other.tags[tag]

    def set_tag(self, tag, item):
        self._tags[tag].append(item)

    def __getitem__(self, item):
        return self._values[item]

    @property
    def tags(self):
        return self._tags.keys()

    @property
    def tag(self):
        return lambda tag: [self._values[key] for key in self._tags[tag]]