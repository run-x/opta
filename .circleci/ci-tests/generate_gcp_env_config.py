import os
import sys

ABSOLUTE_FILE_PATH = os.path.abspath(os.path.dirname(__file__))
AWS_REGIONS = ["us-central1", "us-east1", "us-west1"]

ENV_NAME = sys.argv[1]
input_gcp_region = sys.argv[2]

if input_gcp_region not in AWS_REGIONS:
    sys.exit(1)

GCP_REGION = input_gcp_region

template_environment_file = os.path.join(ABSOLUTE_FILE_PATH, "create-and-destroy-gcp", "template-environment.yml")
template_environment_additional_nodepool_file = os.path.join(ABSOLUTE_FILE_PATH, "create-and-destroy-gcp", "template-environment-additional-nodepool.yml")

environment_file = os.path.join(ABSOLUTE_FILE_PATH, "create-and-destroy-gcp", "environment1.yml")
environment_additional_nodepool_file = os.path.join(ABSOLUTE_FILE_PATH, "create-and-destroy-gcp", "environment-additional-nodepool.yml")

with open(template_environment_file, "r") as f:
    environment_template = f.read()

environment_template = environment_template.replace("GCP_REGION", GCP_REGION)
environment_template = environment_template.replace("ENV_NAME", ENV_NAME)

with open(environment_file, 'w') as f:
    f.write(environment_template)

with open(template_environment_additional_nodepool_file, "r") as f:
    environment_additional_nodepool_template = f.read()

environment_additional_nodepool_template = environment_additional_nodepool_template.replace("GCP_REGION", GCP_REGION)
environment_additional_nodepool_template = environment_additional_nodepool_template.replace("ENV_NAME", ENV_NAME)


with open(environment_additional_nodepool_file, 'w') as f:
    f.write(environment_additional_nodepool_template)
