# import json
# from subprocess import CompletedProcess

# from click.testing import CliRunner
# from pytest_mock import MockFixture

# from opta.cli import inspect
# from opta.utils import fmt_msg


# FAKE_RESOURCES_LIST = fmt_msg("""
#     module.doc_db.aws_docdb_cluster.cluster
#     ~module.doc_db.aws_docdb_cluster_instance.cluster_instances[0]
#     ~module.doc_db.random_password.documentdb_auth
#     ~module.rds.data.aws_db_subnet_group.subnet_group[0]
#     ~module.rds.data.aws_security_group.security_group[0]
#     ~module.rds.aws_rds_cluster.db_cluster
#     ~module.rds.aws_rds_cluster_instance.db_instance[0]
#     ~module.rds.random_password.pg_password
#     ~module.redis.data.aws_security_group.security_group[0]
#     ~module.redis.aws_elasticache_replication_group.redis_cluster
#     ~module.redis.random_password.redis_auth
# """)

# class TestInspect:
#     def test_inspect(self, mocker: MockFixture) -> None:
#         # Mock that the terraform CLI tool exists.
#         mocker.patch("opta.kubectl.is_tool", return_value=True)

#         # Mock terraform state list of resources
#         mocker.patch("opta.inspect._list_resources", return_value=FAKE_RESOURCES_LIST)


#         # Mock aws commands, including fetching the current aws account id.
#         fake_aws_account_id = 1234567890123
#         mocked_caller_identity = json.dumps(
#             {
#                 "UserId": "bla",
#                 "Account": f"{fake_aws_account_id}",
#                 "Arn": "arn:aws:iam::979926061731:user/test",
#             }
#         )
#         mocked_update_kubeconfig = "Updated context arn... in ../.kube/config"
#         mocker.patch(
#             "opta.kubectl.nice_run",
#             side_effect=[
#                 CompletedProcess(None, 0, mocked_caller_identity.encode("utf-8")),  # type: ignore
#                 CompletedProcess(None, 0, mocked_update_kubeconfig.encode("utf-8")),  # type: ignore
#             ],
#         )

#         # Mock fetching the opta env aws account id.
#         mocker.patch(
#             "opta.kubectl._get_cluster_env",
#             return_value=("us-east-1", [fake_aws_account_id]),
#         )
#         runner = CliRunner()
#         result = runner.invoke(configure_kubectl, [])
#         assert result.exit_code == 0
