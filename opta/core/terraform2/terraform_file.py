from typing import Any, Dict, Optional


class TerraformFile:
    def __init__(self) -> None:
        self.providers: Dict[str, dict] = {}
        self.data: Dict[str, Dict[str, dict]] = {}
        self.required_providers: Dict[str, dict] = {}
        self.backend_id: Optional[str] = None
        self.backend: dict = {}
        self.modules: Dict[str, dict] = {}
        self.outputs: Dict[str, str] = {}

    def add_backend(self, type: str, data: dict) -> None:
        if self.backend_id:
            raise ValueError("Cannot add backend if one is already set")

        self.backend = data
        self.backend_id = type

    def add_data(self, type: str, id: str, data: dict) -> None:
        of_type = self.data.setdefault(type, {})
        if id in of_type:
            raise ValueError(f"Cannot add duplicate data resource {type}.{id}")

        of_type[id] = data

    def add_module(self, id: str, data: dict) -> None:
        if id in self.modules:
            raise ValueError(f"Cannot add duplicate module {id}")

        self.modules[id] = data

    def add_output(self, id: str, data: str) -> None:
        if id in self.outputs:
            raise ValueError(f"Cannot add duplicate output {id}")

        self.outputs[id] = data

    def add_provider(self, id: str, data: dict) -> None:
        if id in self.providers:
            raise ValueError(f"Cannot add duplicate provider {id}")

        self.providers[id] = data

    def add_required_provider(self, id: str, data: dict) -> None:
        if id in self.required_providers:
            raise ValueError(f"Cannot add duplicate required provider {id}")

        self.required_providers[id] = data

    def __to_json__(self) -> dict:
        out: Dict[str, Any] = {}

        if self.data:
            out["data"] = self.data

        if self.required_providers:
            out.setdefault("terraform", {})[
                "required_providers"
            ] = self.required_providers

        if self.backend_id:
            out.setdefault("terraform", {})["backend"] = {
                self.backend_id: self.backend,
            }

        if self.providers:
            out["provider"] = self.providers

        if self.modules:
            out["module"] = self.modules

        if self.outputs:
            out["output"] = {id: {"value": value} for id, value in self.outputs.items()}

        return out
