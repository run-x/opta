import os
from io import StringIO
from typing import TYPE_CHECKING, FrozenSet

from modules.base import ModuleProcessor
from opta.core.helm import Helm
from opta.exceptions import UserErrors
from opta.utils import logger, yaml

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class HelmChartProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "helm-chart":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s service"
            )
        super(HelmChartProcessor, self).__init__(module, layer)

    @property
    def required_path_dependencies(self) -> FrozenSet[str]:
        return super().required_path_dependencies | Helm.get_required_path_executables()

    def process(self, module_idx: int) -> None:
        if "repository" in self.module.data and "chart_version" not in self.module.data:
            raise UserErrors(
                "If you specify a remote repository you must give a version."
            )
        values = self.module.data.get("values", {})
        if values:
            stream = StringIO()
            yaml.dump(values, stream)
            logger.debug(
                f"These are the values passed in from the opta yaml:\n{stream.getvalue()}"
            )
        values_file = self.module.data.get("values_file", None)
        values_files = self.module.data.get("values_files", [])
        if values_file is not None and values_files != []:
            raise UserErrors(
                "Can't have values_file and values_files at the same time. Either put all of your files in "
                "values_files or have one single file and put it in values_file"
            )
        if values_file:
            values_files.append(values_file)

        fullpath_values_files = []
        for current_values_file in values_files:
            if not current_values_file.startswith("/"):
                full_path = os.path.join(
                    os.path.dirname(self.layer.path), current_values_file
                )
            else:
                full_path = current_values_file
            fullpath_values_files.append(full_path)

        self.module.data["values_files"] = fullpath_values_files

        super(HelmChartProcessor, self).process(module_idx)
