import os
import shutil
from typing import Any, Mapping

import click
from PyInquirer import prompt

TEMPLATE_DIR = os.environ.get("RUNXC_TEMPLATE_DIR")


@click.command()
def main() -> int:
    """Microservice Generator"""
    print(
        "Welcome to runxc. Please answer the following \
          questions to generate your service."
    )

    questions = [
        {
            "type": "input",
            "name": "name",
            "message": "Service name",
            "default": "myservice",
        },
        {
            "type": "input",
            "name": "outputDir",
            "message": "Output directory",
            "default": lambda x: f"./{x['name']}",
        },
        {
            "type": "list",
            "name": "language",
            "message": "Language",
            "choices": ["python"],
        },
        {
            "type": "confirm",
            "name": "build",
            "message": "Docker build template",
            "default": True,
        },
        {
            "type": "confirm",
            "name": "deploy",
            "message": "Kubernetes deploy template",
            "default": True,
        },
        {
            "type": "confirm",
            "name": "infra",
            "message": "Terraform infra template",
            "default": True,
        },
    ]

    answers = prompt(questions)
    print(answers)
    generate(answers)

    print("Generated!")

    return 0


def generate(answers: Mapping[str, Any]) -> None:
    if os.path.exists(answers["outputDir"]):
        raise Exception("Output dir already exists!")

    # Copy application
    shutil.copytree(
        f"{TEMPLATE_DIR}/application/{answers['language']}", f"{answers['outputDir']}/"
    )

    if answers["build"]:
        # Copy build
        shutil.copytree(f"{TEMPLATE_DIR}/build", f"{answers['outputDir']}/build")

    if answers["deploy"]:
        # Copy deploy
        shutil.copytree(f"{TEMPLATE_DIR}/deploy", f"{answers['outputDir']}/deploy")

    if answers["infra"]:
        # Copy infra
        shutil.copytree(f"{TEMPLATE_DIR}/infra", f"{answers['outputDir']}/infra")


if __name__ == "__main__":
    main()
