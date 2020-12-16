import json
import os
import shutil
import subprocess
from typing import Any, Mapping

import click
from PyInquirer import prompt

TEMPLATE_DIR = os.environ.get("RUNXC_TEMPLATE_DIR")


class Module:
    def __init__(self, path: str):
        self.path = path
        self.config = json.loads(open(f"{path}/module.json").read())
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
            "outputs": self.config["outputs"] if "outputs" in self.config else [],
            "version": self.version,
        }

        if root:
            with open(f"{outputDir}/.runxc.json", "a") as f:
                f.write(json.dumps(out, indent=2))

        return out


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

    Module(TEMPLATE_DIR).execute(outputDir)
    print("Generated!")

    return 0


if __name__ == "__main__":
    cli()
