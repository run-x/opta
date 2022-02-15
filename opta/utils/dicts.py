# utilities on dictionaries

from typing import List, Tuple


def extract(d: dict, key: str) -> Tuple[dict, dict]:
    """extract a key and it's value into a new dictionary
    return a copy of the original dictionary minus the extracted dictionary and the new dictionary
    """
    if key not in d:
        # nothing to extract
        return d, {}

    extract_json = d[key]

    # remove from original and return extracted
    d = d.copy()
    d.pop(key)
    return d, {key: extract_json}


def denormalize(d: dict) -> List[dict]:
    """denormalize a dictionary
    ex: denormalize({a: {b: {}, c: {}}) returns {a: {b: {}}} and {a: {c: {}}}
    """
    result = []
    for k1, v1 in d.items():
        if type(v1) == dict:
            for k2, v2 in v1.items():
                result.append({k1: {k2: v2}})
        else:
            result.append({k1: v1})
    return result


def merge(d1: dict, d2: dict) -> dict:
    """merge dictionaries
    ex: mege({'a': 'aaa'}, {'b': 'bbb'}) returns {'a': 'aaa', 'b': 'bbb'}
    if the same key exist in both dictionary take the value from the first parameter.
    """
    result = {}
    for key, v1 in d1.items():
        # do merge
        if key in d2:
            # do merge
            result[key] = {**d2[key], **v1}
        else:
            result[key] = v1

    for key, v2 in d2.items():
        if key not in result:
            result[key] = v2

    return result
