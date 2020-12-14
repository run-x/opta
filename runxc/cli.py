import json
import os
import shutil
from typing import Any, Mapping

import click
from PyInquirer import prompt

TEMPLATE_DIR = os.environ.get("RUNXC_TEMPLATE_DIR")


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
        {"type": "input", "name": "gcp_project", "message": "GCP project"},
        {"type": "input", "name": "gcp_network", "message": "GCP network"},
        {"type": "input", "name": "terraform_bucket", "message": "Terraform bucket"},
        {"type": "input", "name": "terraform_prefix", "message": "Terraform prefix"},
    ]

    answers = prompt(questions)
    print(answers)
    _generate(answers, overwrite)

    print("Generated!")

    return 0


def _generate(answers: Mapping[str, Any], overwrite: bool) -> None:
    if os.path.exists(answers["outputDir"]):
        if not overwrite:
            raise Exception("Output dir already exists!")
        else:
            shutil.rmtree(answers["outputDir"])

    if TEMPLATE_DIR is None or not os.path.exists(TEMPLATE_DIR):
        raise Exception("Template dir doesn't exist!")

    # Copy application
    shutil.copytree(
        f"{TEMPLATE_DIR}/application/{answers['language']}", f"{answers['outputDir']}/"
    )

    if answers["deploy"]:
        # Copy deploy
        shutil.copytree(f"{TEMPLATE_DIR}/deploy", f"{answers['outputDir']}/deploy")

    if answers["infra"]:
        # Copy infra
        shutil.copytree(f"{TEMPLATE_DIR}/infra", f"{answers['outputDir']}/infra")

    # Generate config
    with open(f"{answers['outputDir']}/runxcconfig.json", "w") as f:
        f.write(
            json.dumps(
                {
                    "service_name": answers["name"],
                    "language": answers["language"],
                    "gen_config": answers,
                    "cloud": "gcp",
                    "gcp_project": answers["gcp_project"],
                    "gcp_network": answers["gcp_network"],
                    "terraform": {
                        "bucket": answers["terraform_bucket"],
                        "prefix": answers["terraform_prefix"],
                    },
                },
                indent=2,
            )
        )

    # TODO README


if __name__ == "__main__":
    cli()
