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


def set_module_field(
    module_type: str, field_path: List[str]
) -> Callable[[dict, str], dict]:
    def applier(d: dict, val: str) -> dict:
        if "modules" not in d:
            d["modules"] = []

        found_modules = [
            module
            for module in d["modules"]
            if "type" in module and module["type"] == module_type
        ]
        if len(found_modules) == 0:
            module = {
                "type": module_type,
            }
            d["modules"].append(module)
        else:
            [module] = found_modules

        apply_field = dictionary_deep_set(field_path)
        apply_field(module, val)
        return d

    return applier
