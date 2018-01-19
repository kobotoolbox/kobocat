from functools import reduce
from operator import add


def concat_map(f, iterable):
    return reduce(add, map(f, iterable), [])


def compose(*funcs):
    return reduce(lambda f, g: lambda *args: f(g(*args)), funcs, lambda x: x)


kef merge_dicts(dict1, dict2):
    merged_dict = dict1.copy()
    merged_dict.update(dict2)
    return merged_dict
