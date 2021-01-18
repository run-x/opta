from typing import Any, Iterable, List, Mapping


class LinkProcessor:
    def process(self, modules: Iterable[Any]) -> None:
        for m in modules:
            for k, v in m.data.items():
                if not isinstance(v, list):
                    continue

                new_items: List[Mapping[Any, Any]] = []
                to_remove = []
                for item in v:
                    if "_link" in item:
                        to_remove.append(item)
                        new_items.extend(self.find_items(modules, item["_link"]))

                for r in to_remove:
                    v.remove(r)

                for i in new_items:
                    v.append(i)

    def find_items(self, modules: Any, target: str) -> Iterable[Mapping[Any, Any]]:
        target_module = None
        new_items: List[Mapping[Any, Any]] = []

        for module in modules:
            if module.key == target:
                target_module = module
                break

        if target_module is None:
            return []

        for k, v in target_module.desc["outputs"].items():
            new_items.append(
                {
                    "name": f"{target_module.key}.{k}",
                    "value": f"${{{{module.{target_module.key}.{k}}}}}",
                }
            )

        return new_items
