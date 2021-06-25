from typing import Callable, List


def dictionary_deep_set(path: List[str]) -> Callable[[dict, str], dict]:
    def applier(d: dict, val: str) -> dict:
        *dict_fields, last_field = path
        curr = d
        for field in dict_fields:
            if field not in curr:
                curr[field] = {}
            curr = curr[field]

        curr[last_field] = val
        return d

    return applier
