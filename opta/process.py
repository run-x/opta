# new-module-api

"""
Contains the module api versions of commands, but these command implementations will probably be moved later
"""

import os
from dataclasses import dataclass
from typing import Any, Dict

import click

from opta.constants import TF_FILE_PATH, TF_PLAN_PATH
from opta.core.cloud2 import AWS
from opta.core.plan_displayer import PlanDisplayer
from opta.core.terraform2 import Terraform, TerraformFile
from opta.loader import LayerLoader, ModuleSpecLoader
from opta.module2 import Module, ModuleProcessor
from opta.module_spec import ModuleSpec
from opta.utils import json, logger
from opta.utils.ref import Reference
from opta.utils.visit import Visitor, fill_missing_list_or_dict


@dataclass
class ApplyOptions:
    auto_approve: bool
    config_path: str
    detailed_plan: bool = False


def apply(options: ApplyOptions) -> None:
    """
    Handles the apply command
    """
    logger.warning(
        "Opta's module API mode is in preview and is NOT READY FOR PRODUCTION USE."
    )
    loader = LayerLoader()

    layer = loader.from_path(options.config_path)

    module_specs = {spec.name: spec for spec in ModuleSpecLoader().load_all()}

    module_map: Dict[str, Module] = {}
    for module in layer.modules:
        module.processor = ModuleProcessor(module.proxy)
        module_map[module.alias] = module

    tf = Terraform()
    # Pull local state into directory and load existing resource data
    tf.download_state(layer)
    tf_config = TerraformFile()

    cloud = AWS()
    cloud.configure_providers(tf_config, layer)

    execution_order = [set([module.alias]) for module in layer.modules]

    for step in execution_order:
        # Ensure consistent execution order
        modules = [module_map[id] for id in sorted(step)]

        for module in modules:
            spec = module_specs[module.type]

            special_references = {
                Reference.parse(ref): value
                for ref, value in {
                    "meta.env": layer.name,  # TODO: Resolve to actual env name once we have multiple opta file support
                    "meta.layer": layer.name,
                    "meta.module": module.alias,
                }.items()
            }

            module_vars = _build_initial_terraform_variables(
                module, spec, special_references
            )

            module.pre_terraform_plan(module_vars)

            if not spec.dir:
                raise ValueError(f"unknown path for module {spec.name}")

            module_vars["source"] = os.path.join(spec.dir, "tf_module")

            tf_config.add_module(module.alias, module_vars)

        write_tf(tf_config)

        targets = [f"module.{id}" for id in step]

        tf.plan(lock=False, targets=targets, out=TF_PLAN_PATH, quiet=False)
        PlanDisplayer.display(detailed_plan=options.detailed_plan)

        if not options.auto_approve:
            click.confirm(
                "The above are the planned changes for your opta run. Do you approve?",
                abort=True,
            )

        for module in modules:
            module.pre_terraform_apply()

        try:
            tf.apply(auto_approve=options.auto_approve, plan=TF_PLAN_PATH, quiet=False)
        finally:
            tf.upload_state(layer)

        for module in modules:
            module.post_terraform_apply()


def write_tf(config: TerraformFile) -> None:
    """
    Writes the terraform manifest file to disk
    """
    path = TF_FILE_PATH
    data = json.dumps(config, indent=2)
    with open(path, "w") as f:
        f.write(data)

    logger.debug(f"Terraform manifest written to {path}")


def _build_initial_terraform_variables(
    module: Module, spec: ModuleSpec, extra_refs: Dict[Reference, Any]
) -> Dict[str, Any]:
    """
    Builds the inital dict containing Terraform's input variables
    """
    vars: Dict[str, Any] = {}

    input_visitor = Visitor(module.input)
    var_visitor = Visitor(vars)

    for conn in spec.input_terraform_connections:
        if conn.source in extra_refs:
            val = extra_refs[conn.source]
        elif conn.source not in input_visitor:
            continue
        else:
            val = input_visitor[conn.source]

        var_visitor.set(
            conn.target,
            val,
            allow_missing_leaf=True,
            fill_missing=fill_missing_list_or_dict,
        )

    return vars
