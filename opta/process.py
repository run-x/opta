import os
from dataclasses import dataclass
from typing import Any, Dict

import click

from opta.constants import TF_FILE_PATH, TF_PLAN_PATH
from opta.core.cloud_provider import AWSProvider
from opta.core.plan_displayer import PlanDisplayer
from opta.core.terraform2 import Terraform, TerraformFile
from opta.linker import Linker
from opta.loader import LayerLoader, ModuleSpecLoader
from opta.module2 import Module, ModuleProcessor
from opta.module_spec import ModuleSpec
from opta.utils import json, logger
from opta.utils.ref import Reference, is_interpolated_reference
from opta.utils.visit import Visitor, fill_missing_list_or_dict


@dataclass
class ApplyOptions:
    auto_approve: bool
    config_path: str
    detailed_plan: bool = False


def apply(options: ApplyOptions) -> None:
    loader = LayerLoader()

    # TODO: Handle local?

    layer = loader.from_path(options.config_path)

    # TODO: Validate cloud credentials
    # TODO: Validate required path dependencies

    # TODO: Pull terraform state
    # TODO: Verify referenced environment exists

    # TODO: Create state storage if it doesn't exist
    # TODO: Generate opta resource tags - Where should this live?

    # TODO: Get cloud client

    # TODO: Check state version issues

    # ---

    module_specs = {spec.name: spec for spec in ModuleSpecLoader().load_all()}

    module_map: Dict[str, Module] = {}

    for module in layer.modules:
        module.processor = ModuleProcessor(module.proxy)
        module_map[module.alias] = module

    linker = Linker(module_specs=module_specs.values())
    result = linker.process(layer)

    # TODO: How do we skip over unchanged modules?
    #   Possible solution: Modules marked as 'idempotent' won't rerun if inputs haven't changed and we have run it successfully on previous inputs

    # TODO: Refactor terraform state

    tf = Terraform()
    tf.download_state(layer)
    tf_config = TerraformFile()

    cloud = AWSProvider()
    cloud.add_provider_config(tf_config, layer)

    # tf_config.add_required_provider("aws", {
    #     "source": "hashicorp/aws",
    #     "version": "3.70.0",
    # })

    for step in result.execution_order:
        # Ensure consistent execution order
        modules = [module_map[id] for id in sorted(step)]

        # TODO: Resolve interpolations in input
        # Until supported, make sure we aren't using any
        for module in modules:
            for ref, value in Visitor(module.input):
                if is_interpolated_reference(value):
                    raise ValueError(f"Interpolated inputs not yet supported ({ref}")

        for module in modules:
            spec = module_specs[module.type]

            special_references = {
                Reference.parse(ref): value
                for ref, value in {
                    "meta.env": "foo",  # TODO: Figure out actual env name
                    "meta.layer": layer.name,
                    "meta.module": module.alias,
                }.items()
            }

            module_vars = _build_initial_terraform_variables(
                module, spec, special_references
            )

            module.pre_terraform_plan(module_vars)

            # TODO: We should be more intelligent with this path. Keep it relative?
            #   What does this look like for "compiled" opta?
            if not spec.dir:
                raise ValueError(f"unknown path for module {spec.name}")

            module_vars["source"] = os.path.join(spec.dir, "tf_module")

            # TODO: How do we define the special variables like env_name, layer_name, and module_name

            tf_config.add_module(module.alias, module_vars)

        # TODO: Render modules in step and run plan

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
            # TODO: Pass in plan details
            module.pre_terraform_apply()

        tf.apply(auto_approve=options.auto_approve, plan=TF_PLAN_PATH, quiet=False)

        for module in modules:
            # TODO: Pass in plan details (and terraform run results?)
            module.post_terraform_apply()


def write_tf(config: TerraformFile) -> None:
    path = TF_FILE_PATH
    data = json.dumps(config, indent=2)
    with open(path, "w") as f:
        f.write(data)

    logger.debug(f"Output written to {path}")


def _build_initial_terraform_variables(
    module: Module, spec: ModuleSpec, extra_refs: Dict[Reference, Any]
) -> Dict[str, Any]:
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
