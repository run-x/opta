import json
import os
import re
import shutil
import subprocess
from typing import Any, Dict, Mapping

import click
from PyInquirer import prompt

TEMPLATE_DIR = os.environ.get("RUNXC_TEMPLATE_DIR")
DEFAULT_ARGUMENTS = (
    json.loads(open(".defaults").read()) if os.path.exists(".defaults") else {}
)


class Module:
    def __init__(self, path: str):
        self.path = path
        self.config = json.loads(open(f"{path}/module.json").read())

        if "arguments" in self.config:
            for a in self.config["arguments"]:
                default = DEFAULT_ARGUMENTS.get(self.config["name"], {}).get(a["name"])
                if default is not None:
                    a["default"] = default

        # TODO should do better than just gitsha
        self.version = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, cwd=path, check=True
            )
            .stdout.decode("utf-8")
            .strip()
        )

    def __str__(self) -> str:
        return self.config["description"]

    def description(self) -> str:
        return self.config["description"]

    def execute(self, outputDir: str, root: bool = True) -> Mapping[str, Any]:
        """
            Print name
            Ask arguments
            Copy files
            Append to readme
            Ask about submodules and recurse
            Add info to root config
        """
        print(self.config["description"])

        arguments = {}
        if "arguments" in self.config:
            arguments = prompt(self.config["arguments"])

        if "files" in self.config:
            for file in self.config["files"]:
                if os.path.isdir(f"{self.path}/{file}"):
                    shutil.copytree(
                        f"{self.path}/{file}", f"{outputDir}/{file}", dirs_exist_ok=True
                    )
                else:
                    shutil.copy(f"{self.path}/{file}", f"{outputDir}/{file}")

        if os.path.exists(f"{self.path}/README.md"):
            with open(f"{outputDir}/README.md", "a") as f:
                f.write(f"# {self.config['description']}\n")
                f.write(open(f"{self.path}/README.md").read())
                f.write("\n\n")

        submodules = list(
            map(
                lambda x: Module(f"{self.path}/{x}"),
                self.config["submodules"] if "submodules" in self.config else [],
            )
        )
        submodules_out = []
        if len(submodules) > 0:
            enabled = prompt(
                {
                    "name": "enabled",
                    "message": "Submodules",
                    "type": "checkbox",
                    "choices": map(
                        lambda x: {"name": x.description(), "value": x}, submodules
                    ),
                }
            )["enabled"]

            for s in enabled:
                submodules_out.append(s.execute(outputDir, False))

        out = {
            "name": self.config["name"],
            "arguments": arguments,
            "submodules": submodules_out,
            "files": self.config["files"] if "files" in self.config else [],
            "outputs": self.config["outputs"] if "outputs" in self.config else {},
            "version": self.version,
        }

        if root:
            with open(f"{outputDir}/.runxc.json", "a") as f:
                root_out = {
                    "version": (
                        subprocess.run(
                            ["git", "rev-parse", "HEAD"], capture_output=True, check=True
                        )
                        .stdout.decode("utf-8")
                        .strip()
                    ),
                    "module": out,
                    "outputs": collect_outputs(out, {}),
                }
                f.write(json.dumps(root_out, indent=2))

        return out


def collect_outputs(module: Dict[str, Any], args: Dict[str, str]) -> Dict[str, str]:
    args = args.copy()
    args.update(module["arguments"] if "arguments" in module else {})

    out = hydrate(module["outputs"] if "outputs" in module else {}, args)

    if "submodules" in module:
        for s in module["submodules"]:
            out.update(collect_outputs(s, args))

    return out


def hydrate(outputs: Dict[str, str], args: Dict[str, str]) -> Dict[str, str]:
    new_out = {}
    for (k, v) in outputs.items():
        new_v = v
        subs = re.findall(r"\{([a-z_]+)\}", v)
        for sub in subs:
            new_v = re.sub(r"\{[a-z_]+\}", args[sub], new_v, count=1)
        new_out[k] = new_v

    return new_out


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option(
    "--overwrite", is_flag=True, default=False, help="Overwrite existing output dir"
)
def gen(overwrite: bool) -> int:
    """Microservice Generator"""
    print(
        "Welcome to runxc. Please answer the following "
        "questions to generate your service."
    )

    if TEMPLATE_DIR is None or not os.path.exists(TEMPLATE_DIR):
        raise Exception("Template dir doesn't exist!")

    outputDir = prompt(
        [{"type": "input", "name": "outputDir", "message": "Output directory"}]
    )["outputDir"]

    if os.path.exists(outputDir):
        raise Exception("Output dir exists")
    else:
        os.mkdir(outputDir)

    Module(TEMPLATE_DIR).execute(outputDir)
    print("Generated!")

    return 0


if __name__ == "__main__":
    cli()
