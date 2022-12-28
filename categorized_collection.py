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

    def __init__(self, items: dict[T, S], tags: dict[str, list[T]]):
        self.tags = defaultdict(list).update(tags)
        self.items = items

    def keys(self):
        yield from self._values.keys()

    def items(self):
        yield from self._values.items()

    def values(self):
        yield from self._values.values()

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