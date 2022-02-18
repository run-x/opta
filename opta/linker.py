# new-module-api

from collections.abc import MutableSequence
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Iterable, List, Set

from opta.layer2 import Layer
from opta.link import Link
from opta.link_spec import InputLinkSpec, OutputLinkSpec
from opta.module2 import Module
from opta.module_spec import ModuleSpec
from opta.utils.ref import (
    InterpolatedReference,
    Reference,
    SimpleInterpolatedReference,
    get_all_references,
    parse_ref_string,
)
from opta.utils.visit import Visitor, fill_missing_list_or_dict

_ModuleMap = Dict[str, Module]


@dataclass
class LinkResult:
    execution_order: List[FrozenSet[str]] = field(default_factory=list)
    interpolations: Dict[str, Dict[Reference, InterpolatedReference]] = field(
        default_factory=dict
    )


class Linker:
    """
    Responsible for forming the links between modules defined in an opta file
    """

    def __init__(self, module_specs: Iterable[ModuleSpec]):
        self._module_specs = {spec.name: spec for spec in module_specs}

    def process(self, layer: Layer) -> LinkResult:
        result = LinkResult()
        module_map = self._module_map(layer.modules)

        result.interpolations = self._pass_interpolation(module_map)

        # Pass: TODO Run validation of input, but ignore defaults or required; assume refs are valid
        # Pass: TODO Make sure that there are no interpolations in the link params

        self._pass_automatic_links(module_map)
        self._pass_add_links_from_interpolation(module_map, result.interpolations)

        # Pass: connect outputs to links; TODO: This might not actually be needed? Can happen during input phase
        # Pass: verify that we don't have any cyclical links

        self._pass_connect_inputs(module_map)
        # Pass: Validate input
        # Pass: Run validation of input, but assume refs are valid
        # Pass: build execution order

        order = self._pass_build_execution_order(module_map)
        result.execution_order = order

        # TODO: Run module processor validate at some point above

        return result

    def _pass_add_links_from_interpolation(
        self,
        modules: _ModuleMap,
        interpolation_map: Dict[str, Dict[Reference, InterpolatedReference]],
    ) -> None:
        """
        Add any links from references in interpolations that we don't already have links for.
        """
        for alias, module in modules.items():
            interpolations = interpolation_map.get(alias, {})
            if not interpolations:
                continue

            referenced_modules: Set[str] = set()
            for path, refs in interpolations.items():
                for ref in get_all_references(refs):
                    if ref[0] != "module":
                        # TODO: Handle different reference paths (e.g. to other layers)
                        continue

                    module_alias = str(ref[1])
                    if module_alias not in modules:
                        raise ValueError(
                            f"Found reference to non-existant module {module_alias} at {path}"
                        )

                    referenced_modules.add(module_alias)

            for module_name in referenced_modules:
                try:
                    module.link_for_module(module_name)
                except KeyError:
                    link = Link(module_name, types=set())
                    module.links.append(link)

    def _pass_automatic_links(self, modules: _ModuleMap) -> None:
        """
        Resolves automatic links in each module
        """
        link_providers: Dict[str, List[str]] = {}

        # TODO: This doesn't handle ordering; if a later module provides the type, we will end up in a linking loop
        # As part of above, don't link automatically if that would create a loop; How do we detect this?

        # Figure out all link types that modules output
        for alias, module in modules.items():
            spec = self._module_specs[module.type]
            for output_link_spec in spec.output_links:
                # TODO: Should we support turning off this automatic linking on the output side?
                type = output_link_spec.type
                link_providers.setdefault(type, []).append(alias)

        # TODO: Don't link a type if that type, or the linked module, was already linked manually by the user
        # TODO: Also don't link automatically if all fields that would be filled by the link are already filled

        # Hook up links automatically if correctly configured
        for module in modules.values():
            self._pass_automatic_links_for_module(modules, module, link_providers)

    def _pass_automatic_links_for_module(
        self,
        all_modules: _ModuleMap,
        module: Module,
        link_providers: Dict[str, List[str]],
    ) -> None:
        """
        Resolves automatic links for a single module.
        """
        already_linked_types = self._check_explicit_links(all_modules, module)

        spec = self._spec_of(module)
        for link_spec in spec.input_links:
            if not link_spec.automatic:
                continue

            # If this link type is already present, don't add it again automatically unless its a multi link
            if link_spec.type in already_linked_types and not link_spec.multiple_target:
                continue

            providers = link_providers.get(link_spec.type, [])

            if not providers:
                continue

            # TODO: Support multiple providers if this is a multi-link
            if len(providers) > 1:
                raise RuntimeError(
                    f"Cannot automatically link type {link_spec.type} since more than 1 module provides it"
                )

            provider = providers[0]

            # TODO: Connect params defaults if defined
            try:
                link = module.link_for_module(provider)
            except KeyError:
                link = Link(provider, types=set())
                module.links.append(link)

            # TODO: Should we be adding the alias or the true type?
            link.add_type(link_spec.alias)

    def _pass_build_execution_order(self, modules: _ModuleMap) -> List[FrozenSet[str]]:
        """
        Calculates and returns the order in which we can run modules by looking at dependencies formed by links.
        If a link cycle exists, raises an error.
        Modules that don't have dependencies between each other will be on the same execution "step" in an unspecified order.
        """
        # Execution steps where modules can run simultaneously
        steps: List[FrozenSet[str]] = []

        # List of modules where we have found in previous execution steps for.
        # Flattened version of `steps` for faster checking
        processed_modules: Set[str] = set()

        # The ids of modules that we haven't been able to figure out where they go yet
        remaining_modules = set(modules.keys())

        while remaining_modules:
            current_step: Set[str] = set()

            for id in remaining_modules:
                module = modules[id]

                is_ready = all(link.name in processed_modules for link in module.links)

                if not is_ready:
                    continue

                current_step.add(id)

            # If nothing got resolved in this step, then we have a cycle somewhere,
            # or there is a reference to a module that doesn't exist, but that shouldn't happen at this point
            if not current_step:
                # TODO: Use more specific error class
                raise RuntimeError(
                    "Link cycle detected in these modules {}".format(
                        ", ".join(remaining_modules)
                    )
                )

            remaining_modules.difference_update(current_step)
            processed_modules.update(current_step)

            steps.append(frozenset(current_step))

        return steps

    def _pass_connect_inputs(self, modules: _ModuleMap) -> None:
        """
        Inspects module links and sets inputs on one module to refrence another
        """
        for module in modules.values():
            self._pass_connect_inputs_for_module(modules, module)

    def _pass_connect_inputs_for_module(
        self, modules: _ModuleMap, module: Module
    ) -> None:
        for link in module.links:
            spec = self._spec_of(module)

            output_module = modules[link.name]
            output_spec = self._spec_of(output_module)

            # `link.types` shouldn't be None at this point, but handle the case to appease the type checker
            # (and for free handle the empty set case, even though that would be handled by the loop)
            if not link.types:
                continue

            for link_type in link.types:
                input_link_spec = spec.input_link_spec_for(link_type)

                # Use actual type here, not just alias
                output_link_spec = output_spec.output_link_spec_for(input_link_spec.type)

                debug_path = f"{module.alias} (link {link.name})"
                conn_map = self._build_connection_map(
                    debug_path, input_link_spec, output_link_spec
                )
                if not conn_map:
                    continue

                input_visitor = Visitor(module.input)

                base_ref = input_link_spec.multiple_target or Reference()
                if base_ref:
                    base_list: MutableSequence
                    try:
                        base_list = input_visitor[base_ref]
                    except (KeyError, IndexError):
                        base_list = []
                        Visitor(module.input).set(
                            base_ref, base_list, fill_missing=fill_missing_list_or_dict
                        )
                    # else:
                    if not isinstance(base_list, MutableSequence):
                        raise RuntimeError(
                            f"Unexpected field type on {debug_path}; expected mutable sequence"
                        )

                    base_data: Dict[str, Any] = {}
                    base_list.append(base_data)

                    input_visitor = Visitor(base_data)

                for input_ref, output_ref in conn_map.items():
                    # TODO: Handle case where input source does not align with output target (either is broader)

                    absolute_output_ref = (
                        SimpleInterpolatedReference("module", link.name, "output")
                        + output_ref
                    )

                    input_visitor.set(
                        input_ref,
                        absolute_output_ref,
                        fill_missing=fill_missing_list_or_dict,
                    )

                # TODO: Validate params
                params = link.params_for(link_type)
                print(f"{debug_path} got params: {params}")
                param_visitor = Visitor(params)
                for conn in input_link_spec.params_connections or []:
                    print(f"{debug_path} connection {conn}")
                    try:
                        value = param_visitor[conn.source]
                    except (KeyError, IndexError):
                        continue

                    input_visitor.set(
                        conn.target, value, fill_missing=fill_missing_list_or_dict
                    )

    def _pass_interpolation(
        self, modules: _ModuleMap
    ) -> Dict[str, Dict[Reference, InterpolatedReference]]:
        """
        Finds all interpolation references in module inputs.
        Parses those values into reference objects for later use.
        Returns a dict of module aliases to dict of input locations to references
        """

        # TODO: Handle differences between simple and compound interp reference strings

        found: Dict[str, Dict[Reference, InterpolatedReference]] = {}

        # TODO: Allow interpolation on link params
        # (Should we? Don't see a reason why not, especially since it can reference layer params)
        # It is a little bit more complicated since we the references are relative to the root of the input,
        # so we would need a way to specify that its a link parameter, and which one.
        for alias, module in modules.items():
            found[alias] = {}

            visitor = Visitor(module.input)
            for ref, value in visitor:
                if not isinstance(value, str):
                    continue

                parsed = parse_ref_string(value)

                if isinstance(parsed, str):
                    continue

                visitor[ref] = parsed
                found[alias][ref] = parsed

        return found

    def _build_connection_map(
        self, dp: str, input_spec: InputLinkSpec, output_spec: OutputLinkSpec
    ) -> Dict[Reference, Reference]:
        # TODO: How are unset values handled?

        if input_spec.connect_all_to and output_spec.connect_all_from:
            return {input_spec.connect_all_to: output_spec.connect_all_from}

        if input_spec.connect_all_to is None and output_spec.connect_all_from is None:
            if not input_spec.connections:
                raise RuntimeError(f"Unexpected empty input connections list on {dp}")

            if not output_spec.connections:
                raise RuntimeError(f"Unexpected empty output connections list on {dp}")

            output_ref_map: Dict[Reference, Reference] = {
                conn.target: conn.source for conn in output_spec.connections
            }

            return {
                conn.target: output_ref_map[conn.source]
                for conn in input_spec.connections
            }

        if input_spec.connect_all_to:
            print(f"TODO: Skipping connect_all_to on {dp}")
            return {}
        elif output_spec.connect_all_from:
            print(f"TODO: Skipping connect_all_from on {dp}")
            return {}

        return {}

    def _check_explicit_links(self, all_modules: _ModuleMap, module: Module) -> Set[str]:
        """
        Checks explicit links for issues.
        Returns set of the link types already in use.
        """
        already_linked_types: Set[str] = set()

        spec = self._spec_of(module)

        for link in module.links:
            if link.name not in all_modules:
                # TODO: "Did you mean x?" could be useful here
                # TODO: How to link to modules in other layers?
                raise ValueError(
                    f"Module {module.alias} has link ({link.name}) to unknown module"
                )

            # Track explicit types
            for type_or_alias in link.types or []:
                # Make sure we are converting to the true type, and not just an alias
                link_spec = spec.input_link_spec_for(type_or_alias)
                link_type = link_spec.type

                if link_type in already_linked_types and not link_spec.multiple_target:
                    raise ValueError(
                        f"Link type {link_type} already in use on {module.alias}"
                    )

                already_linked_types.add(link_spec.type)

        return already_linked_types

    def _module_map(self, modules: Iterable[Module]) -> Dict[str, Module]:
        """
        Converts iterable of modules into mapping of module alias to module.
        Also checks for duplicate aliases and unknown module types.
        """
        module_map: Dict[str, Module] = {}
        for module in modules:
            if module.type not in self._module_specs:
                raise ValueError(f"Unknown module type `{module.type}`")

            if module.alias in module_map:
                raise ValueError(f"Duplicate modules with alias {module.alias}")

            module_map[module.alias] = module

        return module_map

    def _spec_of(self, module: Module) -> ModuleSpec:
        return self._module_specs[module.type]
