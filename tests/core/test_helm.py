from pytest_mock import MockFixture

from opta.core.helm import Helm


class TestHelm:
    MOCK_RELEASE = "mock_release"
    MOCK_NAMESPACE = "mock_namesapce"
    MOCK_REVISION_1 = "1"
    MOCK_REVISION_X = "X"

    def test_rollback_helm_base_revision_1(self, mocker: MockFixture) -> None:
        mock_helm_check = mocker.patch("opta.core.helm.helm_check", return_value=None)
        mock_nice_run_helm_uninstall = mocker.patch("opta.core.helm.nice_run")

        Helm.rollback_helm(
            self.MOCK_RELEASE, self.MOCK_NAMESPACE, revision=self.MOCK_REVISION_1
        )

        mock_helm_check.assert_called_once_with()
        mock_nice_run_helm_uninstall.assert_called_once_with(
            ["helm", "uninstall", self.MOCK_RELEASE, "--namespace", self.MOCK_NAMESPACE],
            check=True,
        )

    def test_rollback_helm_base_revision_x(self, mocker: MockFixture) -> None:
        mock_helm_check = mocker.patch("opta.core.helm.helm_check", return_value=None)
        mock_nice_run_helm_rollback = mocker.patch("opta.core.helm.nice_run")

        Helm.rollback_helm(
            self.MOCK_RELEASE, self.MOCK_NAMESPACE, revision=self.MOCK_REVISION_X
        )

        mock_helm_check.assert_called_once_with()
        mock_nice_run_helm_rollback.assert_called_once_with(
            [
                "helm",
                "rollback",
                self.MOCK_RELEASE,
                self.MOCK_REVISION_X,
                "--namespace",
                self.MOCK_NAMESPACE,
            ],
            check=True,
        )

    def test_get_helm_list_without_namespace(self, mocker: MockFixture) -> None:
        mock_helm_check = mocker.patch("opta.core.helm.helm_check", return_value=None)
        mock_namespace_placeholder = ["--all-namespaces"]
        mock_nice_run_helm_list_process = mocker.patch("opta.core.helm.nice_run")

        mock_json_loads = mocker.patch("opta.core.helm.json.loads")

        Helm.get_helm_list()
        mock_helm_check.assert_called_once_with()
        mock_nice_run_helm_list_process.assert_called_once_with(
            ["helm", "list", "--all", *mock_namespace_placeholder, "-o", "json"],
            capture_output=True,
            check=True,
        )
        mock_json_loads.assert_called_once()

    def test_get_helm_list_with_namespace(self, mocker: MockFixture) -> None:
        mock_helm_check = mocker.patch("opta.core.helm.helm_check", return_value=None)
        mock_namespace_placeholder = ["--namespace", self.MOCK_NAMESPACE]
        mock_nice_run_helm_list_process = mocker.patch("opta.core.helm.nice_run")

        mock_json_loads = mocker.patch("opta.core.helm.json.loads")

        Helm.get_helm_list(namespace=self.MOCK_NAMESPACE)
        mock_helm_check.assert_called_once_with()
        mock_nice_run_helm_list_process.assert_called_once_with(
            ["helm", "list", "--all", *mock_namespace_placeholder, "-o", "json"],
            capture_output=True,
            check=True,
        )
        mock_json_loads.assert_called_once()
