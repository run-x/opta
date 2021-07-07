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

    def test_init_azure(self, mocker: MockFixture) -> None:
        mocked_input = mocker.patch("opta.commands.init_templates.template.input")

        runner = CliRunner()
        mocked_input.side_effect = [
            "opta",
            "run-x",
            "",
            "tenant-id",
            "subscription-id",
        ]
        result = runner.invoke(cli, "init env azure")
        expected_result = """
            name: opta
            org_name: run-x
            providers:
                azurerm:
                    location: uscentral
                    tenant_id: tenant-id
                    subscription_id: subscription-id
            modules:
            - type: base
            - type: k8s-cluster
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
            domain: my.dns.domain
            delegated: false
            - type: k8s-cluster
            max_nodes: 12
            - type: k8s-base
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
            domain: my.dns.domain
            delegated: false
            - type: k8s-cluster
            max_nodes: 12
            - type: k8s-base
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


class TestInitService:
    def test_basic_init(self, mocker: MockFixture) -> None:
        mocked_input = mocker.patch("opta.commands.init_templates.template.input")

        runner = CliRunner()
        mocked_input.side_effect = [
            "my-new-service",
        ]

        example_env_config_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "examples/environments/gcp-env.yml"
        )
        result = runner.invoke(cli, f"init service {example_env_config_path} k8s")
        expected_result = """
        environments:
        - name: gcp-live-example
        path: examples/environments/gcp-env.yml
        variables: {}
        name: my-new-service
        modules:
        - type: k8s-service
        name: app
        port:
            http: 9000
        image: AUTO
        env_vars:
        - name: APPENV
            value: '{env}'
        public_uri: '{parent.domain}'
        resource_request:
            cpu: 100
            memory: 1024
        """
        assert _sanitize(expected_result) in _sanitize(result.output)
