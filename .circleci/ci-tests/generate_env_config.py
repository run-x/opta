import os
import sys


def create_config_from_template(
    provider, directory, template_file, output_file, is_tg=False
):
    template_file = os.path.join(ABSOLUTE_FILE_PATH, directory, template_file)
    output_file = os.path.join(ABSOLUTE_FILE_PATH, directory, output_file)
    with open(template_file, "r") as f:
        template = f.read()

    if provider == "AWS":
        template = template.replace("AWS_REGION", AWS_REGION)
    elif provider == "GCP":
        template = template.replace("GCP_REGION", GCP_REGION)

    if is_tg:
        template = template.replace("ENV_NAME", f"{ENV_NAME}-tg")
    else:
        template = template.replace("ENV_NAME", ENV_NAME)

    with open(output_file, "w") as f:
        f.write(template)


ABSOLUTE_FILE_PATH = os.path.abspath(os.path.dirname(__file__))
AWS_REGIONS = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
GCP_REGIONS = ["us-central1", "us-east1", "us-west1"]

ENV_NAME = sys.argv[1]
input_aws_region = sys.argv[2]
input_gcp_region = sys.argv[3]

if input_aws_region not in AWS_REGIONS:
    sys.exit(1)

if input_gcp_region not in GCP_REGIONS:
    sys.exit(1)

AWS_REGION = input_aws_region
GCP_REGION = input_gcp_region

create_config_from_template(
    "AWS", "create-and-destroy-aws", "template-environment.yml", "environment.yml"
)
create_config_from_template(
    "AWS",
    "create-and-destroy-aws",
    "template-environment-additional-nodegroup.yml",
    "environment-additional-nodegroup.yml",
)
create_config_from_template(
    "AWS",
    "todo-list",
    "template-provider-aws-dns-false.yml",
    "provider-aws-dns-false.yml",
)
create_config_from_template(
    "AWS", "todo-list", "template-provider-aws-dns-true.yml", "provider-aws-dns-true.yml"
)

create_config_from_template(
    "GCP", "create-and-destroy-gcp", "template-environment.yml", "environment.yml"
)
create_config_from_template(
    "GCP",
    "create-and-destroy-gcp",
    "template-environment-additional-nodepool.yml",
    "environment-additional-nodepool.yml",
)
create_config_from_template(
    "GCP", "todo-list", "template-provider-gcp.yml", "provider-gcp.yml"
)
create_config_from_template(
    "AWS",
    "terraform-generated-aws",
    "template-environment.yaml",
    "environment.yaml",
    is_tg=True,
)
create_config_from_template(
    "GCP",
    "terraform-generated-gcp",
    "template-environment.yaml",
    "environment.yaml",
    is_tg=True,
)
create_config_from_template(
    "AZURE", "create-and-destroy-azure", "template-environment.yaml", "environment.yaml"
)
