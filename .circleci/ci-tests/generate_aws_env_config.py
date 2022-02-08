from datetime import date
import os

absolute_path = os.path.abspath(os.path.dirname(__file__))

AWS_REGIONS = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
ENV_NAMES = ["awsenv-ci-0", "awsenv-ci-1", "awsenv-ci-2", "awsenv-ci-3"]

index = date.today().day % 4

AWS_REGION = AWS_REGIONS[index]
ENV_NAME = ENV_NAMES[index]

template_environment_file = os.path.join(absolute_path, "create-and-destroy-aws", "template-environment.yml")
template_environment_additional_nodegroup_file = os.path.join(absolute_path, "create-and-destroy-aws", "template-environment-additional-nodegroup.yml")

environment_file = os.path.join(absolute_path, "create-and-destroy-aws", "environment1.yml")
environment_additional_nodegroup_file = os.path.join(absolute_path, "create-and-destroy-aws", "environment-additional-nodegroup1.yml")

with open(template_environment_file, "r") as f:
    environment_template = f.read()

environment_template = environment_template.replace("AWS_REGION", AWS_REGION)
environment_template = environment_template.replace("ENV_NAME", ENV_NAME)

with open(environment_file, 'w') as f:
    f.write(environment_template)

with open(template_environment_additional_nodegroup_file, "r") as f:
    environment_additional_nodegroup_template = f.read()

environment_additional_nodegroup_template = environment_additional_nodegroup_template.replace("AWS_REGION", AWS_REGION)
environment_additional_nodegroup_template = environment_additional_nodegroup_template.replace("ENV_NAME", ENV_NAME)


with open(environment_additional_nodegroup_file, 'w') as f:
    f.write(environment_additional_nodegroup_template)
