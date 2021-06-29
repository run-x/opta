import os
import re

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.cli import cli


def _sanitize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


class TestInitEnv:
    def test_init_gcp(self, mocker: MockFixture) -> None:
        mocked_input = mocker.patch("opta.commands.init_templates.template.input")

        runner = CliRunner()
        mocked_input.side_effect = [
            "opta",
            "run-x",
            "us-east1",
            "my-project-name",
            "my.dns.domain",
            "no",
        ]
        result = runner.invoke(cli, "init env gcp")
        expected_result = """
        name: opta
        org_name: run-x
        providers:
        google:
            region: us-east1
            project: my-project-name
        modules:
        - type: base
        - type: dns
        domain: my.dns.domain
        delegated: false
        - type: k8s-cluster
        max_nodes: 6
        - type: k8s-base
        """
        assert _sanitize(expected_result) in _sanitize(result.output)

    def test_init_aws(self, mocker: MockFixture) -> None:
        mocked_input = mocker.patch("opta.commands.init_templates.template.input")

        runner = CliRunner()
        mocked_input.side_effect = [
            "opta",
            "run-x",
            "us-west-1",
            "123412341234",
            "my.dns.domain",
            "no",
        ]
        result = runner.invoke(cli, "init env aws")
        expected_result = """
            name: opta
            org_name: run-x
            providers:
            aws:
                region: us-west-1
                account_id: '123412341234'
            modules:
            - type: base
            - type: dns
            delegated: false
            domain: my.dns.domain
            - name: deployeruser
            type: aws-iam-user
            extra_iam_policies:
            - arn:aws:iam::aws:policy/AdministratorAccess
            - name: deployerrole
            type: aws-iam-role
            extra_iam_policies:
            - arn:aws:iam::aws:policy/AdministratorAccess
            allowed_iams:
            - ${{module.deployeruser.user_arn}}
            - type: k8s-cluster
            max_nodes: 12
            - type: k8s-base
            admin_arns:
            - ${{module.deployeruser.user_arn}}
            - ${{module.deployerrole.role_arn}}
        """
        assert _sanitize(expected_result) in _sanitize(result.output)

    def test_use_aws_defaults(self, mocker: MockFixture) -> None:
        mocked_input = mocker.patch("opta.commands.init_templates.template.input")

        runner = CliRunner()
        mocked_input.side_effect = [
            "  ",
            "run-x",
            "  ",
            "123412341234",
            "my.dns.domain",
            "no",
        ]
        result = runner.invoke(cli, "init env aws")
        expected_result = f"""
            name: {os.path.basename(os.getcwd())}
            org_name: run-x
            providers:
            aws:
                region: us-east-1
                account_id: '123412341234'
            modules:
            - type: base
            - type: dns
            delegated: false
            domain: my.dns.domain
            - name: deployeruser
            type: aws-iam-user
            extra_iam_policies:
            - arn:aws:iam::aws:policy/AdministratorAccess
            - name: deployerrole
            type: aws-iam-role
            extra_iam_policies:
            - arn:aws:iam::aws:policy/AdministratorAccess
            allowed_iams:
            - ${{{{module.deployeruser.user_arn}}}}
            - type: k8s-cluster
            max_nodes: 12
            - type: k8s-base
            admin_arns:
            - ${{{{module.deployeruser.user_arn}}}}
            - ${{{{module.deployerrole.role_arn}}}}
        """
        assert _sanitize(expected_result) in _sanitize(result.output)

    def test_use_gcp_defaults(self, mocker: MockFixture) -> None:
        mocked_input = mocker.patch("opta.commands.init_templates.template.input")

        runner = CliRunner()
        mocked_input.side_effect = [
            "  ",
            "run-x",
            "  ",
            "my-project-name",
            "my.dns.domain",
            "no",
        ]
        result = runner.invoke(cli, "init env gcp")
        expected_result = f"""
        name: {os.path.basename(os.getcwd())}
        org_name: run-x
        providers:
        google:
            region: us-central1
            project: my-project-name
        modules:
        - type: base
        - type: dns
        domain: my.dns.domain
        delegated: false
        - type: k8s-cluster
        max_nodes: 6
        - type: k8s-base
        """
        assert _sanitize(expected_result) in _sanitize(result.output)
