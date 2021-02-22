from pytest_mock import MockFixture

from opta.core.terraform import Terraform
from opta.layer import Layer
from opta.utils import fmt_msg
from tests.utils import MockedCmdOut


class TestTerraform:
    def test_init(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.terraform.nice_run")

        # Calling terraform apply should also call terraform init
        tf_init = mocker.patch("opta.core.terraform.Terraform.init")
        Terraform.apply()
        assert tf_init.call_count == 1

        # Calling terraform plan should also call terraform init
        Terraform.plan()
        assert tf_init.call_count == 2

    def test_get_modules(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.terraform.Terraform.download_state", return_value=True)

        tf_state_list_output = fmt_msg(
            """
            ~data.aws_caller_identity.provider
            ~data.aws_eks_cluster_auth.k8s
            ~module.redis.data.aws_security_group.security_group[0]
            ~module.redis.aws_elasticache_replication_group.redis_cluster
            ~module.doc_db.data.aws_security_group.security_group[0]
        """
        )

        mocker.patch(
            "opta.core.terraform.nice_run",
            return_value=MockedCmdOut(tf_state_list_output),
        )
        assert {"redis", "doc_db"} == Terraform.get_existing_modules(
            mocker.Mock(spec=Layer)
        )
