from pytest_mock import MockFixture

from opta.core.helm import Helm


class TestHelm:
    MOCK_RELEASE = "mock_release"
    MOCK_NAMESPACE = "mock_namesapce"
    MOCK_REVISION_1 = "1"
    MOCK_REVISION_X = "X"

    def test_get_required_path_executables(self) -> None:
        deps = Helm.get_required_path_executables()
        assert len(deps) == 1

    def test_rollback_helm_base_revision_1(self, mocker: MockFixture) -> None:
        mock_validate_helm_installed = mocker.patch(
            "opta.core.helm.Helm.validate_helm_installed", return_value=None
        )
        mock_nice_run_helm_uninstall = mocker.patch("opta.core.helm.nice_run")

        Helm.rollback_helm(
            "test-kube-context",
            self.MOCK_RELEASE,
            self.MOCK_NAMESPACE,
            revision=self.MOCK_REVISION_1,
        )

        mock_validate_helm_installed.assert_called_once()
        mock_nice_run_helm_uninstall.assert_called_once_with(
            [
                "helm",
                "uninstall",
                self.MOCK_RELEASE,
                "--kube-context",
                "test-kube-context",
                "--kubeconfig",
                mocker.ANY,
                "--namespace",
                self.MOCK_NAMESPACE,
            ],
            check=True,
        )

    def test_rollback_helm_base_revision_x(self, mocker: MockFixture) -> None:
        mock_validate_helm_installed = mocker.patch(
            "opta.core.helm.Helm.validate_helm_installed", return_value=None
        )
        mock_nice_run_helm_rollback = mocker.patch("opta.core.helm.nice_run")

        Helm.rollback_helm(
            "test-kube-context",
            self.MOCK_RELEASE,
            self.MOCK_NAMESPACE,
            revision=self.MOCK_REVISION_X,
        )

        mock_validate_helm_installed.assert_called_once()
        mock_nice_run_helm_rollback.assert_called_once_with(
            [
                "helm",
                "rollback",
                self.MOCK_RELEASE,
                self.MOCK_REVISION_X,
                "--kube-context",
                "test-kube-context",
                "--kubeconfig",
                mocker.ANY,
                "--namespace",
                self.MOCK_NAMESPACE,
            ],
            check=True,
        )

    def test_get_helm_list_without_namespace(self, mocker: MockFixture) -> None:
        mock_validate_helm_installed = mocker.patch(
            "opta.core.helm.Helm.validate_helm_installed", return_value=None
        )
        mock_namespace_placeholder = ["--all-namespaces"]
        mock_nice_run_helm_list_process = mocker.patch("opta.core.helm.nice_run")

        mock_json_loads = mocker.patch("opta.core.helm.json.loads")

        Helm.get_helm_list("test-kube-context")
        mock_validate_helm_installed.assert_called_once()
        mock_nice_run_helm_list_process.assert_called_once_with(
            [
                "helm",
                "list",
                "--all",
                "--kube-context",
                "test-kube-context",
                "--kubeconfig",
                mocker.ANY,
                *mock_namespace_placeholder,
                "-o",
                "json",
            ],
            capture_output=True,
            check=True,
        )
        mock_json_loads.assert_called_once()

    def test_get_helm_list_with_namespace(self, mocker: MockFixture) -> None:
        mock_validate_helm_installed = mocker.patch(
            "opta.core.helm.Helm.validate_helm_installed", return_value=None
        )
        mock_namespace_placeholder = ["--namespace", self.MOCK_NAMESPACE]
        mock_nice_run_helm_list_process = mocker.patch("opta.core.helm.nice_run")

        mock_json_loads = mocker.patch("opta.core.helm.json.loads")

        Helm.get_helm_list("test-kube-context", namespace=self.MOCK_NAMESPACE)
        mock_validate_helm_installed.assert_called_once()
        mock_nice_run_helm_list_process.assert_called_once_with(
            [
                "helm",
                "list",
                "--all",
                "--kube-context",
                "test-kube-context",
                "--kubeconfig",
                mocker.ANY,
                *mock_namespace_placeholder,
                "-o",
                "json",
            ],
            capture_output=True,
            check=True,
        )
        mock_json_loads.assert_called_once()
