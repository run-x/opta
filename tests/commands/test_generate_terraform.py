import os
import tempfile
import uuid
from typing import Generator, List

import pytest
from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.amplitude import AmplitudeClient, amplitude_client
from opta.cli import cli

tmp_dir = ""


@pytest.fixture(autouse=True)
def run_before_and_after_tests(mocker: MockFixture) -> Generator:
    """Fixture to execute asserts before and after a test is run"""
    # Setup
    mocked_boto_client = mocker.patch("opta.core.terraform.boto3.client")
    mocked_boto_client2 = mocker.patch("opta.core.aws.boto3.client")
    mocked_load_kube_config = mocker.patch("opta.core.kubernetes.load_kube_config")
    mocked_set_kube_config = mocker.patch("opta.core.kubernetes.set_kube_config")

    directory = tempfile.TemporaryDirectory(prefix="opta-gen-tf")

    global tmp_dir
    tmp_dir = directory.name
    os.rmdir(tmp_dir)

    with directory:
        yield  # this is where the testing happens

    # Teardown
    # no actual kubernetes/cloud needed
    mocked_boto_client.assert_not_called()
    mocked_boto_client2.assert_not_called()
    mocked_load_kube_config.assert_not_called()
    mocked_set_kube_config.assert_not_called()
    tmp_dir = ""


def test_generate_terraform_env(mocker: MockFixture) -> None:
    env_file = os.path.join(
        os.getcwd(), "tests", "fixtures", "dummy_data", "aws_env_getting_started.yaml"
    )

    mocked_amplitude_client = mocker.patch(
        "opta.commands.generate_terraform.amplitude_client", spec=AmplitudeClient
    )
    mocked_amplitude_client.START_GEN_TERRAFORM_EVENT = (
        amplitude_client.START_GEN_TERRAFORM_EVENT
    )
    mocked_amplitude_client.FINISH_GEN_TERRAFORM_EVENT = (
        amplitude_client.FINISH_GEN_TERRAFORM_EVENT
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "generate-terraform",
            "-c",
            env_file,
            "-d",
            tmp_dir,
            "--auto-approve",
            "--readme-format",
            "md",
        ],
    )
    assert result.exit_code == 0
    assert "Terraform files generated successfully" in result.output

    # check what was created
    _check_file_exist(
        "readme-staging.md",
        [
            "# Terraform stack staging",
            "## Check the backend configuration",
            "## Initialize Terraform",
            "## Execute Terraform for module base",
            "## Execute Terraform for module k8scluster",
            "## Execute Terraform for module k8sbase",
            "## Execute Terraform for the services",
            "## Destroy",
            "terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.base",
            "terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.k8scluster",
            "terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.k8sbase",
            "terraform apply -compact-warnings -auto-approve tf.plan",
            "terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.base -target=module.k8scluster -target=module.k8sbase -destroy",
            "This file was generated by",
        ],
    )
    _check_file_exist(
        "data.tf.json", ["aws_caller_identity", "aws_region", "aws_eks_cluster_auth"]
    )
    _check_file_exist(
        "output.tf.json",
        ["kms_account_key_arn", "vpc_id", "k8s_cluster_name", "load_balancer_raw_dns"],
    )
    _check_file_exist(
        "provider.tf.json",
        ["helm", "cluster_ca_certificate", "aws", "allowed_account_ids"],
    )
    _check_file_exist(
        "terraform.tf.json",
        ["hashicorp/aws", "hashicorp/helm", "./tfstate/staging.tfstate"],
    )
    _check_file_exist(
        "module-base.tf.json",
        [
            # source is now local
            "./modules/aws_base/tf_module",
            "total_ipv4_cidr_block",
        ],
    )
    _check_file_exist(
        "module-k8scluster.tf.json",
        [
            "k8scluster",
            '"source": "./modules/aws_eks/tf_module"',
            '"env_name": "staging"',
            '"vpc_id": "${module.base.vpc_id}"',
            "module.base",
        ],
    )
    _check_file_exist(
        "module-k8sbase.tf.json",
        [
            "k8sbase",
            '"source": "./modules/aws_k8s_base/tf_module"',
            '"module_name": "k8sbase"',
            "module.k8scluster",
        ],
    )
    # this file would only be created if some config was not moved to some individual file (provider, data, output...)
    # right now, it's always empty but if this test fails we would review if something has changed
    assert not os.path.exists(os.path.join(tmp_dir, "staging.tf.json"))

    # check modules were copied over
    _check_file_exist("modules/aws_base/tf_module/vpc.tf", ["aws_vpc"])
    _check_file_exist("modules/aws_eks/tf_module/eks.tf", ["aws_eks_cluster"])
    _check_file_exist("modules/aws_k8s_base/tf_module/ingress_nginx.tf", ["aws_lb"])

    mocked_amplitude_client.send_event.assert_has_calls(
        [
            mocker.call(
                amplitude_client.START_GEN_TERRAFORM_EVENT,
                event_properties={
                    "total_resources": 0,
                    "org_name": "opta-tests",
                    "layer_name": "staging",
                    "parent_name": "",
                    "modules": "aws-base,aws-eks,aws-k8s-base",
                    "success": True,
                },
            ),
            mocker.call(
                amplitude_client.FINISH_GEN_TERRAFORM_EVENT,
                event_properties={
                    "total_resources": 0,
                    "org_name": "opta-tests",
                    "layer_name": "staging",
                    "parent_name": "",
                    "modules": "aws-base,aws-eks,aws-k8s-base",
                    "success": True,
                },
            ),
        ]
    )


def test_generate_terraform_service(mocker: MockFixture) -> None:
    service_file = os.path.join(
        os.getcwd(), "tests", "fixtures", "dummy_data", "aws_service_getting_started.yaml"
    )
    existing_file = _random_file()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "generate-terraform",
            "-c",
            service_file,
            "-d",
            tmp_dir,
            "--delete",
            "--auto-approve",
        ],
    )
    assert result.exit_code == 0
    assert "Terraform files generated successfully" in result.output
    assert (
        "the output directory doesn't include terraform files for the environment"
        in result.output
    )

    # check existing file was deleted
    _check_file_not_exist(existing_file)

    # check what was created
    _check_file_exist(
        "readme-hello.html",
        [
            "Terraform stack hello",
            "Check the backend configuration",
            "Initialize Terraform",
            "Execute Terraform for module hello",
            "Destroy",
            "terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.hello",
            "terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.hello -destroy",
            "terraform apply -compact-warnings -auto-approve tf.plan",
            "This file was generated by",
        ],
    )
    _check_file_exist(
        "data.tf.json",
        [
            "aws_caller_identity",
            "aws_region",
            "aws_eks_cluster_auth",
            # use data from the env stack, exported locally
            "terraform_remote_state",
            '"backend": "local"',
            '"path": "./tfstate/staging.tfstate"',
        ],
    )
    _check_file_exist(
        "output.tf.json", ["docker_repo_url", "module.hello.docker_repo_url"]
    )
    _check_file_exist(
        "provider.tf.json",
        ["helm", "cluster_ca_certificate", "aws", "allowed_account_ids"],
    )
    _check_file_exist(
        "terraform.tf.json",
        [
            "hashicorp/aws",
            "hashicorp/helm",
            # always use the env name for the tf file, this allows exporting many opta config together in the same directory
            "./tfstate/staging.tfstate",
        ],
    )
    # the env terraform files are not generated for a service
    _check_file_not_exist("module-base.tf.json")
    _check_file_not_exist("module-k8scluster.tf.json")
    _check_file_not_exist("module-k8sbase.tf.json")

    # this file would only be created if some config was not moved to some individual file (providers, data, output...)
    # right now, it's always empty but if this test fails we would review if something has changed
    assert not os.path.exists(os.path.join(tmp_dir, "helo.tf.json"))

    # check modules were copied over
    _check_file_exist(
        "modules/aws_k8s_service/tf_module/main.tf",
        [
            'resource "helm_release" "k8s-service"',
            'chart = "${path.module}/../../opta-k8s-service-helm"',
        ],
    )
    _check_file_not_exist("modules/aws_eks/")
    _check_file_not_exist("modules/aws_k8s_base/")

    # check helm chart
    _check_file_exist(
        "modules/opta-k8s-service-helm/templates/deployment.yaml", ["kind: Deployment"]
    )


def test_generate_terraform_env_and_service(mocker: MockFixture) -> None:
    # when generating terraform files for an env and a service, some terraform files are merged to prevent some terraform error
    # ex: there can only be one provider named 'aws' defined
    env_file = os.path.join(
        os.getcwd(), "tests", "fixtures", "dummy_data", "aws_env_getting_started.yaml"
    )

    service_file = os.path.join(
        os.getcwd(), "tests", "fixtures", "dummy_data", "aws_service_getting_started.yaml"
    )

    runner = CliRunner()

    # run for env
    result = runner.invoke(
        cli, ["generate-terraform", "-c", env_file, "-d", tmp_dir, "--auto-approve"]
    )
    assert result.exit_code == 0
    assert "Terraform files generated successfully" in result.output

    # run for service - same output directory
    result = runner.invoke(
        cli,
        [
            "generate-terraform",
            "-c",
            service_file,
            "-d",
            tmp_dir,
            "--readme-format",
            "none",
            "--auto-approve",
        ],
    )
    assert result.exit_code == 1
    assert "Output directory already exists" in str(result.exception)

    # run for service - same output directory using --delete
    result = runner.invoke(
        cli,
        [
            "generate-terraform",
            "-c",
            service_file,
            "-d",
            tmp_dir,
            "--readme-format",
            "none",
            "--delete",
            "--auto-approve",
        ],
    )
    assert result.exit_code == 0

    # check readme files were not created because `--readme-format none`
    _check_file_not_exist("staging.md")
    _check_file_not_exist("hello.html")

    _check_file_exist(
        "data.tf.json",
        [
            "aws_caller_identity",
            "aws_region",
            "aws_eks_cluster_auth",
            "terraform_remote_state",
            '"backend": "local"',
            '"path": "./tfstate/staging.tfstate"',
        ],
    )
    _check_file_exist(
        "output.tf.json",
        [
            # this file contains fields from service
            "docker_repo_url",
            "module.hello.docker_repo_url",
        ],
    )
    _check_file_exist(
        "provider.tf.json",
        ["helm", "cluster_ca_certificate", "aws", "allowed_account_ids"],
    )
    _check_file_exist(
        "terraform.tf.json",
        ["hashicorp/aws", "hashicorp/helm", "./tfstate/staging.tfstate"],
    )
    _check_file_not_exist("modules/aws_base/")
    _check_file_not_exist("modules/aws_eks/")
    _check_file_exist("modules/aws_k8s_service/")
    _check_file_exist("modules/opta-k8s-service-helm/")


def test_generate_terraform_undefined_dir(mocker: MockFixture) -> None:
    service_file = os.path.join(
        os.getcwd(), "tests", "fixtures", "dummy_data", "aws_service_getting_started.yaml"
    )

    # the value is empty
    directory = " "

    runner = CliRunner()
    result = runner.invoke(
        cli, ["generate-terraform", "-c", service_file, "-d", directory, "--delete"]
    )
    assert result.exit_code != 0
    assert "Error: --directory can't be empty" in result.output


def test_generate_terraform_dir_already_exist(mocker: MockFixture) -> None:
    service_file = os.path.join(
        os.getcwd(), "tests", "fixtures", "dummy_data", "aws_service_getting_started.yaml"
    )

    runner = CliRunner()

    # start with an existing dir with some files
    directory = tmp_dir
    _random_file()

    # except an error, even if--auto-aprove is not set,
    result = runner.invoke(
        cli, ["generate-terraform", "-c", service_file, "-d", directory]
    )
    assert result.exit_code == 1
    assert "Output directory already exists" in str(result.exception)

    # if --delete is set, except a confirmation message before deleting
    result = runner.invoke(
        cli, ["generate-terraform", "-c", service_file, "-d", directory, "--delete"]
    )
    assert result.exit_code != 0
    assert "The output directory will be deleted:" in result.output
    assert "Do you approve?" in result.output

    # if --delete is set and there is a tfstate folder, except a custom confirmation message before deleting
    os.mkdir(os.path.join(directory, "tfstate"))
    result = runner.invoke(
        cli, ["generate-terraform", "-c", service_file, "-d", directory, "--delete"]
    )
    assert result.exit_code != 0
    # custom message
    assert (
        "The output directory will be deleted, including terraform state files:"
        in result.output
    )
    assert "Do you approve?" in result.output


def test_generate_terraform_unsupported_module(mocker: MockFixture) -> None:
    # this file has a aws-dns module which is currently not exportable
    env_file = os.path.join(
        os.getcwd(), "tests", "fixtures", "dummy_data", "aws_env_dns.yaml"
    )

    mocked_amplitude_client = mocker.patch(
        "opta.commands.generate_terraform.amplitude_client", spec=AmplitudeClient
    )
    mocked_amplitude_client.START_GEN_TERRAFORM_EVENT = (
        amplitude_client.START_GEN_TERRAFORM_EVENT
    )
    mocked_amplitude_client.FINISH_GEN_TERRAFORM_EVENT = (
        amplitude_client.FINISH_GEN_TERRAFORM_EVENT
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "generate-terraform",
            "-c",
            env_file,
            "-d",
            tmp_dir,
            "--auto-approve",
            "--readme-format",
            "md",
        ],
    )
    assert result.exit_code == 0
    assert (
        "Terraform files partially generated, a few modules are not supported: aws-dns"
        in result.output
    )

    # check what was created
    _check_file_exist(
        "readme-staging.md",
        [
            "Terraform stack staging",
            "Exporting module dns is not supported at this time.",
            # includes the custom export documentation
            "Follow these [instructions](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring.html) to configure the DNS.",
        ],
    )

    # we still copy the unsupported module files
    _check_file_exist("module-dns.tf.json")
    _check_file_exist("modules/aws_dns/tf_module/main.tf")

    mocked_amplitude_client.send_event.assert_has_calls(
        [
            mocker.call(
                amplitude_client.START_GEN_TERRAFORM_EVENT,
                event_properties={
                    "total_resources": 0,
                    "org_name": "opta-tests",
                    "layer_name": "staging",
                    "parent_name": "",
                    "modules": "aws-base,aws-eks,aws-k8s-base,aws-dns",
                    "unsupported_modules": "aws-dns",
                    "success": True,
                },
            ),
            mocker.call(
                amplitude_client.FINISH_GEN_TERRAFORM_EVENT,
                event_properties={
                    "total_resources": 0,
                    "org_name": "opta-tests",
                    "layer_name": "staging",
                    "parent_name": "",
                    "modules": "aws-base,aws-eks,aws-k8s-base,aws-dns",
                    "unsupported_modules": "aws-dns",
                    "success": True,
                },
            ),
        ]
    )


def test_generate_terraform_remote_backend(mocker: MockFixture) -> None:

    env_file = os.path.join(
        os.getcwd(), "tests", "fixtures", "dummy_data", "aws_env_getting_started.yaml"
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "generate-terraform",
            "-c",
            env_file,
            "-d",
            tmp_dir,
            "--auto-approve",
            "--backend",
            "remote",
            "--readme-format",
            "md",
        ],
    )
    assert result.exit_code == 0
    assert "Terraform files generated successfully" in result.output

    # check what was created
    _check_file_exist(
        "readme-staging.md",
        ["Terraform stack staging", "point to the remote backend used by opta"],
    )
    # check the remote backend is configured
    _check_file_exist(
        "terraform.tf.json",
        [
            '"s3"',
            '"bucket": "opta-tf-state-opta-tests-staging',  # ignoring suffix
            '"dynamodb_table": "opta-tf-state-opta-tests-staging',  # ignoring suffix
        ],
    )


def _check_file_exist(rel_path: str, text_to_find: List[str] = []) -> None:
    file = os.path.join(tmp_dir, rel_path)
    assert os.path.exists(file)
    if text_to_find:
        with open(file) as f:
            output = f.read()
            for text in text_to_find:
                assert text in output, f"Can't find [{text}] in {file}"


def _check_file_not_exist(rel_path: str) -> None:
    file = os.path.join(tmp_dir, rel_path)
    assert not os.path.exists(file)


def _random_file() -> str:
    "_random_file in current directory"
    os.mkdir(tmp_dir)
    new_file = os.path.join(tmp_dir, str(uuid.uuid4()))
    with open(new_file, "w"):
        pass
    return new_file
