from collections.abc import Iterable, Mapping

# function to allow us to convert namedtuple data hierarchy into JSON-able
# form (i.e., into tuples, dictionaries, primitives)
def serialise(obj):
    """Convert a hierarchy of namedtuples into primitives and dicts.

    This function recursively traverses a hierarchy of iterables, looking for
    namedtuple objects and converting them into dictionaries. The resulting
    object should then be parseable as valid JSON.

    """
    if isinstance(obj, Iterable):
        # handle namedtuples
        if hasattr(obj, '_asdict'):
            _dict = dict()
            items = obj._asdict()
            for item in items:
                if isinstance(items[item], Iterable):
                    _dict[item] = serialise(items[item])
                else:
                    _dict[item] = items[item]        
            return _dict

        # handle strings
        if not isinstance(obj, str):
            return tuple(serialise(item) for item in obj)

        # fall through case?
        return obj

    else:
        return obj

def remove_value_none(d):
    """Recursively traverse Mapping to remove keys with value None."""
    _dict = dict()
    for key in d:
        val = d[key]
        if isinstance(val, Mapping):
            _dict[key] = remove_value_none(val)
        elif val is not None:
            _dict[key] = val
    return _dict
