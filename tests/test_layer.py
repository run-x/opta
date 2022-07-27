# type: ignore

import os
from types import SimpleNamespace

import pytest
from pytest_mock import MockFixture

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors
from opta.layer import Layer


class TestLayer:
    def test_infinite_loop_prevention(self):
        with pytest.raises(UserErrors):
            Layer.load_from_yaml(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "infinite_loop.yaml",
                ),
                None,
            )

    def test_same_name_as_parent(self):
        with pytest.raises(UserErrors):
            Layer.load_from_yaml(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "same_name_as_parent.yaml",
                ),
                None,
            )

    def test_hydration_aws(self, mocker: MockFixture):
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "opta-tf-state-opta-tests-dummy-parent-195d"
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        assert layer.metadata_hydration() == {
            "aws": SimpleNamespace(region="us-east-1", account_id="011111111111"),
            "env": "dummy-parent",
            "kubeconfig": "~/.kube/config",
            "layer_name": "dummy-config-1",
            "parent": SimpleNamespace(
                kms_account_key_arn="${data.terraform_remote_state.parent.outputs.kms_account_key_arn}",
                kms_account_key_id="${data.terraform_remote_state.parent.outputs.kms_account_key_id}",
                vpc_id="${data.terraform_remote_state.parent.outputs.vpc_id}",
                private_subnet_ids="${data.terraform_remote_state.parent.outputs.private_subnet_ids}",
                public_subnets_ids="${data.terraform_remote_state.parent.outputs.public_subnets_ids}",
                s3_log_bucket_name="${data.terraform_remote_state.parent.outputs.s3_log_bucket_name}",
                public_nat_ips="${data.terraform_remote_state.parent.outputs.public_nat_ips}",
                zone_id="${data.terraform_remote_state.parent.outputs.zone_id}",
                name_servers="${data.terraform_remote_state.parent.outputs.name_servers}",
                domain="${data.terraform_remote_state.parent.outputs.domain}",
                cert_arn="${data.terraform_remote_state.parent.outputs.cert_arn}",
                k8s_endpoint="${data.terraform_remote_state.parent.outputs.k8s_endpoint}",
                k8s_version="${data.terraform_remote_state.parent.outputs.k8s_version}",
                k8s_ca_data="${data.terraform_remote_state.parent.outputs.k8s_ca_data}",
                k8s_cluster_name="${data.terraform_remote_state.parent.outputs.k8s_cluster_name}",
                k8s_openid_provider_url="${data.terraform_remote_state.parent.outputs.k8s_openid_provider_url}",
                k8s_openid_provider_arn="${data.terraform_remote_state.parent.outputs.k8s_openid_provider_arn}",
                k8s_node_group_security_id="${data.terraform_remote_state.parent.outputs.k8s_node_group_security_id}",
                load_balancer_raw_dns="${data.terraform_remote_state.parent.outputs.load_balancer_raw_dns}",
                load_balancer_arn="${data.terraform_remote_state.parent.outputs.load_balancer_arn}",
                providers="${data.terraform_remote_state.parent.outputs.providers}",
            ),
            "parent_name": "dummy-parent",
            "state_storage": "opta-tf-state-opta-tests-dummy-parent-195d",
            "variables": SimpleNamespace(),
            "vars": SimpleNamespace(),
            "k8s_access_token": None,
            "region": "us-east-1",
        }

    def test_hydration_gcp(self, mocker: MockFixture):
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "opta-tf-state-opta-tests-gcp-dummy-parent"
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "gcp_dummy_config.yaml"
            ),
            None,
        )
        mocked_gcp_class = mocker.patch("opta.layer.GCP")
        mocked_gcp = mocker.Mock()
        mocked_gcp_class.return_value = mocked_gcp
        mocked_credentials = mocker.Mock()
        mocked_gcp.get_credentials.return_value = [mocked_credentials]
        mocked_credentials.token = "blah"
        assert layer.metadata_hydration() == {
            "env": "gcp-dummy-parent",
            "kubeconfig": "~/.kube/config",
            "google": SimpleNamespace(region="us-central1", project="jds-throwaway-1"),
            "layer_name": "gcp-dummy-config",
            "parent": SimpleNamespace(
                kms_account_key_id="${data.terraform_remote_state.parent.outputs.kms_account_key_id}",
                vpc_id="${data.terraform_remote_state.parent.outputs.vpc_id}",
                vpc_self_link="${data.terraform_remote_state.parent.outputs.vpc_self_link}",
                private_subnet_id="${data.terraform_remote_state.parent.outputs.private_subnet_id}",
                private_subnet_self_link="${data.terraform_remote_state.parent.outputs.private_subnet_self_link}",
                k8s_master_ipv4_cidr_block="${data.terraform_remote_state.parent.outputs.k8s_master_ipv4_cidr_block}",
                public_nat_ips="${data.terraform_remote_state.parent.outputs.public_nat_ips}",
                zone_id="${data.terraform_remote_state.parent.outputs.zone_id}",
                zone_name="${data.terraform_remote_state.parent.outputs.zone_name}",
                name_servers="${data.terraform_remote_state.parent.outputs.name_servers}",
                domain="${data.terraform_remote_state.parent.outputs.domain}",
                delegated="${data.terraform_remote_state.parent.outputs.delegated}",
                cert_self_link="${data.terraform_remote_state.parent.outputs.cert_self_link}",
                k8s_endpoint="${data.terraform_remote_state.parent.outputs.k8s_endpoint}",
                k8s_ca_data="${data.terraform_remote_state.parent.outputs.k8s_ca_data}",
                k8s_cluster_name="${data.terraform_remote_state.parent.outputs.k8s_cluster_name}",
                load_balancer_raw_ip="${data.terraform_remote_state.parent.outputs.load_balancer_raw_ip}",
                providers="${data.terraform_remote_state.parent.outputs.providers}",
            ),
            "parent_name": "gcp-dummy-parent",
            "state_storage": "opta-tf-state-opta-tests-gcp-dummy-parent",
            "variables": SimpleNamespace(),
            "vars": SimpleNamespace(),
            "k8s_access_token": "blah",
            "region": mocker.ANY,
        }

    def test_get_event_properties(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )

        assert layer.get_event_properties() == {
            "layer_name": "dummy-config-1",
            "module_aws_documentdb": 2,
            "module_aws_dynamodb": 1,
            "module_aws_k8s_service": 2,
            "module_aws_postgres": 2,
            "module_aws_redis": 2,
            "org_name": "opta-tests",
            "parent_name": "dummy-parent",
            "total_resources": 9,
        }

    def test_parent(self, mocker: MockFixture, monkeypatch):
        mocked_datadog_processor = mocker.patch(
            "modules.datadog.datadog.DatadogProcessor"
        )
        mocked_k8s_base_processor = mocker.patch(
            "modules.aws_k8s_base.aws_k8s_base.AwsK8sBaseProcessor"
        )
        mocked_eks_processor = mocker.patch("modules.aws_eks.aws_eks.AwsEksProcessor")
        mocked_dns_processor = mocker.patch("modules.aws_dns.aws_dns.AwsDnsProcessor")
        mocked_aws_email_processor = mocker.patch(
            "modules.aws_ses.aws_ses.AwsEmailProcessor"
        )
        mocked_aws_documentdb_processor = mocker.patch(
            "modules.aws_documentdb.aws_documentdb.AwsDocumentDbProcessor"
        )
        mocked_base_processor = mocker.patch("opta.layer.ModuleProcessor")

        def mock_get_processor_class(module_type: str) -> ModuleProcessor:

            mock_dict = {}
            mock_dict["datadog"] = mocked_datadog_processor
            mock_dict["aws-k8s-base"] = mocked_k8s_base_processor
            mock_dict["aws-eks"] = mocked_eks_processor
            mock_dict["aws-dns"] = mocked_dns_processor
            mock_dict["aws-ses"] = mocked_aws_email_processor
            mock_dict["aws-documentdb"] = mocked_aws_documentdb_processor

            if module_type in mock_dict:
                return mock_dict[module_type]
            else:
                return mocked_base_processor

        monkeypatch.setattr("opta.layer.get_processor_class", mock_get_processor_class)
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )

        assert layer.name == "dummy-parent"
        assert layer.parent is None
        assert layer == layer.root()
        assert len(layer.modules) == 7
        assert layer.pre_hook(6) is None
        assert layer.post_hook(6, None) is None
        mocked_datadog_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_k8s_base_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_eks_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_dns_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_aws_email_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_base_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )

    def test_child(self, mocker: MockFixture, monkeypatch):
        mocked_datadog_processor = mocker.patch(
            "modules.datadog.datadog.DatadogProcessor"
        )
        mocked_k8s_base_processor = mocker.patch(
            "modules.aws_k8s_base.aws_k8s_base.AwsK8sBaseProcessor"
        )
        mocked_eks_processor = mocker.patch("modules.aws_eks.aws_eks.AwsEksProcessor")
        mocked_dns_processor = mocker.patch("modules.aws_dns.aws_dns.AwsDnsProcessor")
        mocked_k8s_service_processor = mocker.patch(
            "modules.aws_k8s_service.aws_k8s_service.AwsK8sServiceProcessor"
        )
        mocked_aws_email_processor = mocker.patch(
            "modules.aws_ses.aws_ses.AwsEmailProcessor"
        )
        mocked_aws_documentdb_processor = mocker.patch(
            "modules.aws_documentdb.aws_documentdb.AwsDocumentDbProcessor"
        )
        mocked_base_processor = mocker.patch("opta.layer.ModuleProcessor")
        mocked_aws_iam_role_processor = mocker.patch(
            "modules.aws_iam_role.aws_iam_role.AwsIamRoleProcessor"
        )
        mocked_aws_iam_user_processor = mocker.patch(
            "modules.aws_iam_user.aws_iam_user.AwsIamUserProcessor"
        )
        mocked_aws_sqs_processor = mocker.patch("modules.aws_sqs.aws_sqs.AwsSqsProcessor")
        mocked_aws_sns_processor = mocker.patch("modules.aws_sns.aws_sns.AwsSnsProcessor")

        def mock_get_processor_class(module_type: str) -> ModuleProcessor:
            mock_dict = {}
            mock_dict["datadog"] = mocked_datadog_processor
            mock_dict["aws-k8s-base"] = mocked_k8s_base_processor
            mock_dict["aws-eks"] = mocked_eks_processor
            mock_dict["aws-dns"] = mocked_dns_processor
            mock_dict["aws-ses"] = mocked_aws_email_processor
            mock_dict["aws-documentdb"] = mocked_aws_documentdb_processor
            mock_dict["aws-k8s-service"] = mocked_k8s_service_processor
            mock_dict["aws-iam-role"] = mocked_aws_iam_role_processor
            mock_dict["aws-iam-user"] = mocked_aws_iam_user_processor
            mock_dict["aws-sqs"] = mocked_aws_sqs_processor
            mock_dict["aws-sns"] = mocked_aws_sns_processor
            if module_type in mock_dict:
                return mock_dict[module_type]
            else:
                return mocked_base_processor

        monkeypatch.setattr("opta.layer.get_processor_class", mock_get_processor_class)
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )

        assert layer.name == "dummy-config-1"
        assert layer.parent is not None
        assert layer.parent == layer.root()
        assert len(layer.modules) == 17
        assert layer.pre_hook(13) is None
        assert layer.post_hook(13, None) is None

        mocked_k8s_service_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )

        mocked_aws_documentdb_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )

        mocked_base_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
        mocked_aws_iam_role_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
        mocked_aws_iam_user_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
        mocked_aws_sns_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
        mocked_aws_sqs_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )

    def test_check_module_dirs_exist(self):
        from opta.layer import PROCESSOR_DICT, get_processor_class

        for opta_module, processor in PROCESSOR_DICT.items():
            module_class = get_processor_class(opta_module)
            assert module_class.__name__ == processor

    def test_service_missing_env_file(self):
        with pytest.raises(UserErrors) as exception:
            Layer.load_from_yaml(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "tests",
                    "fixtures",
                    "sample_opta_files",
                    "service_missing_env_file.yaml",
                ),
                None,
            )
        assert "Could not find file" in str(exception.value)
        assert "opta-not-found.yml" in str(exception.value)

    def test_service_env_alternate_ext(self):
        # reference an env file using .yml but the file on the disk is .yaml
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "tests",
                "fixtures",
                "sample_opta_files",
                "service_env_alternate_ext.yaml",
            ),
            None,
        )
        assert layer.name == "app"
        assert layer.parent.name == "dummy-parent"

    def test_service_github_repo_env(self, mocker: MockFixture):
        mocker.patch("git.Repo.clone_from")
        git_repo_mocked = mocker.patch("git.Repo.clone_from")
        service_github_repo_env = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "tests",
            "fixtures",
            "sample_opta_files",
            "service_github_repo_env.yaml",
        )
        # use local file for parent instead of cloning a github repo
        dummy_config_parent = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "tests",
            "fixtures",
            "dummy_data",
            "dummy_config_parent.yaml",
        )
        mocker.patch(
            "opta.layer.check_opta_file_exists",
            side_effect=[service_github_repo_env, dummy_config_parent],
        )

        layer = Layer.load_from_yaml(service_github_repo_env, None,)
        git_repo_mocked.assert_called_once_with(
            "git@github.com:run-x/runx-infra.git", mocker.ANY, branch="main", depth=1
        )

        assert layer.name == "app"
        assert layer.parent.name == "dummy-parent"

    def test_service_persistent_storage(self, mocker: MockFixture):

        mocker.patch("opta.core.terraform.nice_run")
        mocker.patch("opta.core.terraform.AWS")
        mocked_delete_persistent_volume_claims = mocker.patch(
            "opta.core.kubernetes.delete_persistent_volume_claims"
        )

        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "tests",
                "fixtures",
                "sample_opta_files",
                "service.yaml",
            ),
            None,
        )
        layer.post_delete(0)

        # check if delete pvc was NOT called
        mocked_delete_persistent_volume_claims.assert_not_called()

        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "tests",
                "fixtures",
                "sample_opta_files",
                "service_persistent_storage.yaml",
            ),
            None,
        )
        layer.post_delete(0)
        # check if delete pvc was called
        mocked_delete_persistent_volume_claims.assert_called_once()

    def test_state_storage(self, mocker: MockFixture):
        mocked_bucket_exists = mocker.patch("opta.layer.Layer.bucket_exists")
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        mocked_bucket_exists.return_value = True
        assert layer.state_storage() == "opta-tf-state-opta-tests-dummy-parent"
        mocked_bucket_exists.return_value = False
        assert layer.state_storage() == "opta-tf-state-opta-tests-dummy-parent-195d"
