import json
import logging
from subprocess import DEVNULL, PIPE
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from opta.amplitude import amplitude_client
from opta.core.aws import AWS, get_aws_resource_id
from opta.exceptions import UserErrors
from opta.nice_subprocess import nice_run
from opta.utils import deep_merge, logger

if TYPE_CHECKING:
    from opta.layer import Layer


class Terraform:
    # True if terraform.tfstate is downloaded.
    downloaded_state: Dict[str, bool] = {}

    @classmethod
    def init(cls, *tf_flags: str) -> None:
        nice_run(["terraform", "init", *tf_flags], check=True)

    # Get outputs of the current terraform state
    @classmethod
    def get_outputs(cls, layer: "Layer") -> dict:
        if not cls.downloaded_state.get(layer.name, False):
            success = cls.download_state(layer)
            if not success:
                raise UserErrors(
                    "Could not fetch remote terraform state, assuming no resources exist yet."
                )
        state = cls.get_state()
        outputs = state.get("outputs", {})
        cleaned_outputs = {}
        for k, v in outputs.items():
            cleaned_outputs[k] = v.get("value")
        return cleaned_outputs

    # Get the full terraform state.
    @classmethod
    def get_state(cls, state_file: str = "./terraform.tfstate") -> dict:
        with open(state_file, "r") as file:
            raw_state = file.read().replace("\n", "")
        return json.loads(raw_state)

    @classmethod
    def apply(
        cls,
        layer: "Layer",
        *tf_flags: str,
        no_init: Optional[bool] = False,
        quiet: Optional[bool] = False,
    ) -> None:
        if not no_init:
            cls.init()
        kwargs: Dict[str, Any] = {}
        if quiet:
            kwargs["stderr"] = PIPE
            kwargs["stdout"] = DEVNULL
        try:
            nice_run(["terraform", "apply", *tf_flags], check=True, **kwargs)
        except Exception as e:
            logging.error(e)
            logging.info("Terraform apply failed, rolling back stale resources.")
            cls.rollback(layer)

    @classmethod
    def rollback(cls, layer: "Layer") -> None:
        amplitude_client.send_event(amplitude_client.ROLLBACK_EVENT)

        aws_resources = AWS(layer).get_opta_resources()
        terraform_resources = set(cls.get_existing_resources(layer))

        # Import all stale resources into terraform state (so they can be destroyed later).
        stale_resources = []
        for resource in aws_resources:
            if resource in terraform_resources:
                continue

            try:
                resource_id = get_aws_resource_id(aws_resources[resource])
                cls.import_resource(resource, resource_id)
                stale_resources.append(resource)
            except Exception:
                logging.debug(
                    f"Resource {resource_id} failed to import. It probably no longer exists, skipping."
                )
                continue

        # Skip destroy if no resources are stale.
        if len(stale_resources) == 0:
            return None

        # Destroy stale terraform resources.
        cls.destroy_resources(layer, stale_resources)

    @classmethod
    def import_resource(cls, tf_resource_address: str, aws_resource_id: str) -> None:
        nice_run(
            ["terraform", "import", tf_resource_address, aws_resource_id], check=True
        )

    @classmethod
    def refresh(cls, *tf_flags: str) -> None:
        nice_run(["terraform", "refresh", *tf_flags], check=True)

    @classmethod
    def destroy_resources(
        cls, layer: "Layer", target_resources: List[str], *tf_flags: str
    ) -> None:
        # If no targets are passed, "terraform destroy" attempts to destroy ALL
        # resources, which should be avoided unless explicitly done.
        if len(target_resources) == 0:
            raise Exception(
                "Target resources was specified to be destroyed, but contained an empty list"
            )

        # Refreshing the state is necessary to update terraform outputs.
        # This includes fetching the latest EKS cluster auth token, which is
        # necessary for destroying many k8s resources.
        cls.refresh()

        for module in reversed(layer.modules):
            module_address_prefix = f"module.{module.name}"
            module_resources = [
                resource
                for resource in target_resources
                if module_address_prefix in resource
            ]
            if len(module_resources) == 0:
                continue

            hosted_zone_resource = "module.awsdns.aws_route53_zone.public"
            if hosted_zone_resource in module_resources:
                cls.destroy_hosted_zone_resources(layer)

            resource_targets = [f"-target={resource}" for resource in module_resources]
            nice_run(["terraform", "destroy", *resource_targets, *tf_flags], check=True)

    @classmethod
    def destroy_all(cls, layer: "Layer", *tf_flags: str) -> None:
        cls.refresh()

        for module in reversed(layer.modules):
            module_address_prefix = f"module.{module.name}"

            hosted_zone_resource = "module.awsdns.aws_route53_zone.public"
            if hosted_zone_resource.startswith(module_address_prefix):
                cls.destroy_hosted_zone_resources(layer)

            nice_run(
                ["terraform", "destroy", f"-target={module_address_prefix}", *tf_flags],
                check=True,
            )

    # The hosted zone resource must often be explicitly destroyed b/c records are created
    # as a side effect of the "external-dns" helm chart.
    # We must destroy the generated records AND the hosted zone itself, or else the helm
    # chart will attempt to re-populate the deleted records in the existing hosted zone.
    @classmethod
    def destroy_hosted_zone_resources(cls, layer: "Layer") -> None:
        hosted_zone_resource = "module.awsdns.aws_route53_zone.public"
        terraform_state = fetch_terraform_state_resources(layer)
        if hosted_zone_resource in terraform_state:
            zone_id = terraform_state[hosted_zone_resource]["zone_id"]
            cls.remove_from_state(hosted_zone_resource)
            AWS.delete_hosted_zone(zone_id)

    # Remove a resource from the terraform state, but does not destroy it.
    @classmethod
    def remove_from_state(cls, resource_address: str) -> None:
        nice_run(["terraform", "state", "rm", resource_address])

    @classmethod
    def plan(cls, *tf_flags: str, quiet: Optional[bool] = False) -> None:
        cls.init()
        kwargs: Dict[str, Any] = {}
        if quiet:
            kwargs["stderr"] = PIPE
            kwargs["stdout"] = DEVNULL
        nice_run(["terraform", "plan", *tf_flags], check=True, **kwargs)

    @classmethod
    def show(cls, *tf_flags: str) -> None:
        nice_run(["terraform", "show", *tf_flags], check=True)

    @classmethod
    def get_existing_modules(cls, layer: "Layer") -> Set[str]:
        existing_resources = cls.get_existing_resources(layer)
        return set(map(lambda r: r.split(".")[1], existing_resources))

    @classmethod
    def get_existing_resources(cls, layer: "Layer") -> List[str]:
        if not cls.downloaded_state.get(layer.name, False):
            success = cls.download_state(layer)
            if not success:
                logger.info(
                    "Could not fetch remote terraform state, assuming no resources exist yet."
                )
                return []

        resource_state = (
            nice_run(["terraform", "state", "list"], check=True, capture_output=True)
            .stdout.decode("utf-8")
            .split("\n")
        )
        # Filter out all `data.*` sources. Only care about module resources
        module_resources = [r for r in resource_state if r.startswith("module")]
        # Sometimes module resource addresses may have [0] or [1] at the end, remove it.
        module_resources = list(
            map(lambda r: r[0 : r.find("[")] if "[" in r else r, module_resources)
        )

        return module_resources

    @classmethod
    def download_state(
        cls, layer: "Layer", state_file: str = "./terraform.tfstate"
    ) -> bool:
        providers = layer.gen_providers(0)
        if "s3" in providers.get("terraform", {}).get("backend", {}):
            bucket = providers["terraform"]["backend"]["s3"]["bucket"]
            key = providers["terraform"]["backend"]["s3"]["key"]
            logger.debug(
                f"Found an s3 backend in bucket {bucket} and key {key}, "
                "gonna try to download the statefile from there"
            )
            s3 = boto3.client("s3")
            try:
                s3.download_file(bucket, key, state_file)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    # The object does not exist.
                    return False
                raise

        cls.downloaded_state[layer.name] = True
        return True

    @classmethod
    def create_state_storage(cls, layer: "Layer") -> None:
        """
        Idempotently create remote storage for tf state
        """
        providers = layer.gen_providers(0)
        if "s3" in providers.get("terraform", {}).get("backend", {}):
            bucket_name = providers["terraform"]["backend"]["s3"]["bucket"]
            dynamodb_table = providers["terraform"]["backend"]["s3"]["dynamodb_table"]
            region = providers["terraform"]["backend"]["s3"]["region"]
            s3 = boto3.client("s3")
            dynamodb = boto3.client("dynamodb", config=Config(region_name=region))
            iam = boto3.client("iam", config=Config(region_name=region))
            try:
                s3.get_bucket_encryption(Bucket=bucket_name,)
            except ClientError as e:
                if e.response["Error"]["Code"] == "AccessDenied":
                    raise UserErrors(
                        f"We were unable to access the S3 bucket, {bucket_name} on your AWS account (opta needs this to store state)."
                        "Usually, it means that the name in your opta.yml is not unique. Try updating it to something else."
                        "It could also mean that your AWS account has insufficient permissions."
                        "Please fix these issues and try again!"
                    )
                if e.response["Error"]["Code"] != "NoSuchBucket":
                    raise UserErrors(
                        "When trying to determine the status of the state bucket, we got an "
                        f"{e.response['Error']['Code']} error with the message "
                        f"{e.response['Error']['Message']}"
                    )
                logger.info("S3 bucket for terraform state not found, creating a new one")
                if region == "us-east-1":
                    s3.create_bucket(Bucket=bucket_name,)
                else:
                    s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": region},
                    )
                s3.put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        "Rules": [
                            {
                                "ApplyServerSideEncryptionByDefault": {
                                    "SSEAlgorithm": "AES256"
                                },
                            },
                        ]
                    },
                )
                s3.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True,
                        "RestrictPublicBuckets": True,
                    },
                )

            try:
                dynamodb.describe_table(TableName=dynamodb_table)
            except ClientError as e:
                if e.response["Error"]["Code"] != "ResourceNotFoundException":
                    raise UserErrors(
                        "When trying to determine the status of the state dynamodb table, we got an "
                        f"{e.response['Error']['Code']} error with the message "
                        f"{e.response['Error']['Message']}"
                    )
                print("Dynamodb table for terraform state not found, creating a new one")
                dynamodb.create_table(
                    TableName=dynamodb_table,
                    KeySchema=[{"AttributeName": "LockID", "KeyType": "HASH"}],
                    AttributeDefinitions=[
                        {"AttributeName": "LockID", "AttributeType": "S"},
                    ],
                    BillingMode="PROVISIONED",
                    ProvisionedThroughput={
                        "ReadCapacityUnits": 20,
                        "WriteCapacityUnits": 20,
                    },
                )
            # Create the service linked roles
            try:
                iam.create_service_linked_role(
                    AWSServiceName="autoscaling.amazonaws.com",
                )
            except ClientError as e:
                if e.response["Error"]["Code"] != "InvalidInput":
                    raise UserErrors(
                        "When trying to create the aws service linked role for autoscaling, we got an "
                        f"{e.response['Error']['Code']} error with the message "
                        f"{e.response['Error']['Message']}"
                    )
                print("Autoscaling service linked role present")
            try:
                iam.create_service_linked_role(
                    AWSServiceName="elasticloadbalancing.amazonaws.com",
                )
            except ClientError as e:
                if e.response["Error"]["Code"] != "InvalidInput":
                    raise UserErrors(
                        "When trying to create the aws service linked role for load balancing, we got an "
                        f"{e.response['Error']['Code']} error with the message "
                        f"{e.response['Error']['Message']}"
                    )
                print("Load balancing service linked role present")


def get_terraform_outputs(layer: "Layer", pull_state: bool = True) -> dict:
    """ Fetch terraform outputs from existing TF file """
    if not pull_state:
        Terraform.init()
    current_outputs = Terraform.get_outputs(layer)
    parent_outputs = _fetch_parent_outputs(pull_state)
    return deep_merge(current_outputs, parent_outputs)


def _fetch_parent_outputs(pull_state: bool = True) -> dict:
    # Fetch the terraform state
    state = Terraform.get_state()

    # Fetch any parent remote states
    resources = state.get("resources", [])
    parent_states = [
        resource
        for resource in resources
        if resource.get("type") == "terraform_remote_state"
    ]

    # Grab all outputs from each remote state and save it.
    parent_state_outputs = {}
    for parent in parent_states:
        parent_outputs = (
            parent["instances"][0]
            .get("attributes", {})
            .get("outputs", {})
            .get("value", {})
        )
        for k, v in parent_outputs.items():
            parent_name = parent.get("name")
            output_name = f"{parent_name}.{k}"
            parent_state_outputs[output_name] = v

    return parent_state_outputs


def fetch_terraform_state_resources(layer: "Layer") -> dict:
    Terraform.download_state(layer)
    state = Terraform.get_state()

    resources = state.get("resources", [])

    resources_dict: Dict[str, dict] = {}
    for resource in resources:
        # Note that resource addresses should start with "module.", but in the
        # saved terraform state, it is already part of the module name.
        # Ex. "module.awsbase"
        address = ".".join(
            [
                resource.get("module", ""),
                resource.get("type", ""),
                resource.get("name", ""),
            ]
        )
        if address == "..":
            continue

        # Some resources like module.awsdns.aws_acm_certificate.certificate have
        # an empty instances list.
        if len(resource["instances"]) == 0:
            resources_dict[address] = {}
        else:
            resources_dict[address] = resource["instances"][0]["attributes"]

        resources_dict[address]["module"] = resource.get("module", "")
        resources_dict[address]["type"] = resource.get("type", "")
        resources_dict[address]["name"] = resource.get("name", "")

    return resources_dict
