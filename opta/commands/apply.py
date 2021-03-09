from threading import Thread
from typing import Optional, Set

import click

from opta.amplitude import amplitude_client
from opta.constants import TF_PLAN_PATH
from opta.core.generator import gen, gen_opta_resource_tags
from opta.core.kubernetes import tail_module_log, tail_namespace_events
from opta.core.terraform import Terraform
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import is_tool, logger


@click.command()
@click.option(
    "-c", "--config", default="opta.yml", help="Opta config file", show_default=True
)
@click.option(
    "-e",
    "--env",
    default=None,
    help="The env to use when loading the config file",
    show_default=True,
)
@click.option(
    "--refresh",
    is_flag=True,
    default=False,
    help="Run from first block, regardless of current state",
    hidden=True,
)
@click.option(
    "--max-module", default=None, type=int, help="Max module to process", hidden=True
)
@click.option(
    "--image-tag",
    default=None,
    type=str,
    help="If this handles a service, it's the image tag you wanna deploy",
)
@click.option(
    "--test",
    is_flag=True,
    default=False,
    help="Run tf plan, but don't lock state file",
    hidden=True,
)
def apply(
    config: str,
    env: Optional[str],
    refresh: bool,
    max_module: Optional[int],
    image_tag: Optional[str],
    test: bool,
) -> None:
    """Initialize your environment or service to match the config file"""
    _apply(config, env, refresh, max_module, image_tag, test)


def _apply(
    config: str,
    env: Optional[str],
    refresh: bool,
    max_module: Optional[int],
    image_tag: Optional[str],
    test: bool,
) -> None:
    if not is_tool("terraform"):
        raise UserErrors("Please install terraform on your machine")
    amplitude_client.send_event(amplitude_client.START_GEN_EVENT)
    layer = Layer.load_from_yaml(config, env)
    layer.variables["image_tag"] = image_tag
    Terraform.create_state_storage(layer)
    gen_opta_resource_tags(layer)

    existing_modules: Set[str] = set()
    for module_idx, current_modules, total_block_count in gen(layer):
        if module_idx == 0:
            # This is set during the first iteration, since the tf file must exist.
            existing_modules = Terraform.get_existing_modules(layer)
        configured_modules = set([x.name for x in current_modules])
        is_last_module = module_idx == total_block_count - 1
        has_new_modules = not configured_modules.issubset(existing_modules)
        if not is_last_module and not has_new_modules and not refresh:
            continue
        if is_last_module:
            untouched_modules = existing_modules - configured_modules
            configured_modules = configured_modules.union(untouched_modules)

        targets = list(map(lambda x: f"-target=module.{x}", sorted(configured_modules)))

        if test:
            Terraform.plan("-lock=false", *targets)
            print("Plan ran successfully, not applying since this is a test.")
        else:
            amplitude_client.send_event(
                amplitude_client.APPLY_EVENT, event_properties={"module_idx": module_idx}
            )
            logger.info("Planning your changes (might take a minute)")
            Terraform.plan(
                "-lock=false",
                "-input=false",
                f"-out={TF_PLAN_PATH}",
                *targets,
                quiet=True,
            )
            Terraform.show(TF_PLAN_PATH)
            click.confirm(
                "The above are the planned changes for your opta run. Do you approve?",
                abort=True,
            )
            logger.info("Applying your changes (might take a minute)")
            if image_tag is not None:
                service_modules = layer.get_module_by_type("k8s-service", module_idx)
                if len(service_modules) != 0:
                    service_module = service_modules[0]
                    # Tailing logs
                    logger.info(
                        f"Identified deployment for kubernetes service module {service_module.name}, tailing logs now."
                    )
                    new_thread = Thread(
                        target=tail_module_log,
                        args=(layer, service_module.name, 10, 2),
                        daemon=True,
                    )
                    # Tailing events
                    new_thread.start()
                    new_thread = Thread(
                        target=tail_namespace_events, args=(layer, 0, 1), daemon=True,
                    )
                    new_thread.start()
            Terraform.apply(layer, TF_PLAN_PATH, no_init=True, quiet=False)
            logger.info("Opta updates complete!")
