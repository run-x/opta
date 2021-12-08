import json

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.output import _load_extra_aws_outputs, _load_extra_gcp_outputs, output
from opta.layer import Layer

TERRAFORM_STATE = {
    "resources": [
        {
            "address": "data.terraform_remote_state.parent",
            "mode": "data",
            "type": "terraform_remote_state",
            "name": "parent",
            "instances": [
                {
                    "attributes": {
                        "outputs": {
                            "value": {
                                "k8s_cluster_name": "main",
                                "k8s_endpoint": "https://bla.bla.bla.eks.amazonaws.com",
                                "state_bucket_arn": "arn:aws:s3:::opta-tf-state-runx-staging",
                                "state_bucket_id": "opta-tf-state-runx-staging",
                            },
                        }
                    }
                }
            ],
            "provider_name": "terraform.io/builtin/terraform",
            "schema_version": 0,
        }
    ]
}


TERRAFORM_OUTPUTS = {
    "bucket_arn": "arn:aws:s3:::runx-test-bucket-runx-staging",
    "bucket_id": "runx-test-bucket-runx-staging",
    "docker_repo_url": "889760294590.dkr.ecr.us-east-1.amazonaws.com/test-service-runx-app",
}


def test_output_aws(mocker: MockFixture) -> None:
    # Opta file check
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    mocker.patch("opta.cli.os.remove")
    mocked_layer_class = mocker.patch("opta.commands.output.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.cloud = "aws"
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocker.patch("opta.commands.output.gen_all")
    mocker.patch("opta.core.terraform.Terraform.get_state", return_value=TERRAFORM_STATE)
    mocker.patch(
        "opta.core.terraform.Terraform.get_outputs", return_value=TERRAFORM_OUTPUTS
    )
    mocker.patch("opta.commands.output._load_extra_aws_outputs", wraps=lambda y: y)

    runner = CliRunner()
    result = runner.invoke(output)
    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "parent.k8s_cluster_name": "main",
        "parent.k8s_endpoint": "https://bla.bla.bla.eks.amazonaws.com",
        "parent.state_bucket_arn": "arn:aws:s3:::opta-tf-state-runx-staging",
        "parent.state_bucket_id": "opta-tf-state-runx-staging",
        "bucket_arn": "arn:aws:s3:::runx-test-bucket-runx-staging",
        "bucket_id": "runx-test-bucket-runx-staging",
        "docker_repo_url": "889760294590.dkr.ecr.us-east-1.amazonaws.com/test-service-runx-app",
    }


def test_output_gcp(mocker: MockFixture) -> None:
    # Opta file check
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    mocker.patch("opta.cli.os.remove")
    mocked_layer_class = mocker.patch("opta.commands.output.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.cloud = "google"
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocker.patch("opta.commands.output.gen_all")
    mocker.patch("opta.core.terraform.Terraform.get_state", return_value=TERRAFORM_STATE)
    mocker.patch(
        "opta.core.terraform.Terraform.get_outputs", return_value=TERRAFORM_OUTPUTS
    )
    mocker.patch("opta.commands.output._load_extra_gcp_outputs", wraps=lambda y: y)

    runner = CliRunner()
    result = runner.invoke(output)
    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "parent.k8s_cluster_name": "main",
        "parent.k8s_endpoint": "https://bla.bla.bla.eks.amazonaws.com",
        "parent.state_bucket_arn": "arn:aws:s3:::opta-tf-state-runx-staging",
        "parent.state_bucket_id": "opta-tf-state-runx-staging",
        "bucket_arn": "arn:aws:s3:::runx-test-bucket-runx-staging",
        "bucket_id": "runx-test-bucket-runx-staging",
        "docker_repo_url": "889760294590.dkr.ecr.us-east-1.amazonaws.com/test-service-runx-app",
    }


def test_load_extra_aws_outputs(mocker: MockFixture) -> None:
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.cloud = "aws"
    mocked_layer.gen_providers.return_value = {"provider": {"aws": {"region": "blah"}}}
    mocked_root = mocker.Mock()
    mocked_layer.root.return_value = mocked_root
    mocked_root.name = "baloney"
    assert _load_extra_aws_outputs(current_outputs={"load_balancer_raw_dns": "ghi"}) == {
        "load_balancer_raw_dns": "ghi"
    }


def test_load_extra_gcp_outputs(mocker: MockFixture) -> None:
    assert _load_extra_gcp_outputs({}) == {}
    assert _load_extra_gcp_outputs({"load_balancer_raw_ip": "1.2.3.4"}) == {
        "load_balancer_raw_ip": "1.2.3.4"
    }
    assert _load_extra_gcp_outputs({"parent.load_balancer_raw_ip": "1.2.3.4"}) == {
        "load_balancer_raw_ip": "1.2.3.4"
    }
