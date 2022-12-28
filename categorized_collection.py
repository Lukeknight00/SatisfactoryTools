from collections import defaultdict
from enum import Flag
from typing import ParamSpec, Type, Any

T = ParamSpec("T")
S = ParamSpec("S")


def FlagDict:
    values: dict
    flags: Type[Flag]

    def __init__(self, values: dict[Any, set[Any]], flags: Type[Flag])
        pass

    def _flag_values(self, flag: Flag):
        return [f for f in self.flags if f in flag]

    def __getitem__(self, item):
        pass

    def __setitem__(self, key, value):
        for
        pass



class CategorizedCollection:
    """
    Class  that stores a dictionary and categories for each of its items. This allows
    access to items directly, as well as by category.
    """
    _values: dict
    _tags: dict

    def __init__(self, items: dict[T, S], tags: dict[str, list[T]]):
        # tags are str: list[item_key]
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