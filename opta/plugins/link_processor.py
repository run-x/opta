from typing import Any, Iterable, List, Mapping

from opta.module import Module


class LinkProcessor:
    def process(self, modules: Iterable[Module]) -> None:
        for m in modules:
            new_items: List[Mapping[Any, Any]] = []
            if "link" in m.data:
                for target in m.data["link"]:
                    new_items.extend(self.find_items(modules, target))

                if "env_vars" not in m.data:
                    m.data["env_vars"] = []

                for i in new_items:
                    m.data["env_vars"].append(i)

            # Look at _link for backwards compatibility
            if "env_vars" in m.data:
                new_items = []
                to_remove: List[Mapping[Any, Any]] = []
                for item in m.data["env_vars"]:
                    if "_link" in item:
                        to_remove.append(item)
                        new_items.extend(self.find_items(modules, item["_link"]))

                for r in to_remove:
                    m.data["env_vars"].remove(r)
                for i in new_items:
                    m.data["env_vars"].append(i)

    def find_items(
        self, modules: Iterable[Module], target: str
    ) -> Iterable[Mapping[Any, Any]]:
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
                    "name": f"{target_module.key}_{k}",
                    "value": f"${{{{module.{target_module.key}.{k}}}}}",
                }
            )

        return new_items
