from click.testing import CliRunner
from kubernetes.client import CoreV1Api, V1Pod, V1PodList
from pytest_mock import MockFixture

from opta.cli import cli
from opta.layer import Layer


def test_shell(mocker: MockFixture) -> None:
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    mocked_layer_class = mocker.patch("opta.commands.shell.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.name = "layer_name"
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    layer_gen_all = mocker.patch("opta.commands.shell.gen_all")
    set_kube_config = mocker.patch("opta.commands.shell.set_kube_config")
    load_kube_config = mocker.patch("opta.commands.shell.load_opta_kube_config")

    mocked_core_v1_api_class = mocker.patch("opta.commands.shell.CoreV1Api")
    mocked_core_v1_api = mocker.Mock(spec=CoreV1Api)
    mocked_core_v1_api_class.return_value = mocked_core_v1_api

    mocked_v1_pod = mocker.Mock(spec=V1Pod)
    mocked_v1_pod.metadata.name = "pod_name"
    mocked_v1_pod_list = mocker.Mock(spec=V1PodList)
    mocked_v1_pod_list.items = [mocked_v1_pod]
    mocked_core_v1_api.list_namespaced_pod.return_value = mocked_v1_pod_list

    mocked_nice_run = mocker.patch("opta.commands.shell.nice_run")

    runner = CliRunner()
    result = runner.invoke(cli, ["shell"])

    assert result.exit_code == 0
    layer_gen_all.assert_called_once_with(mocked_layer)
    set_kube_config.assert_called_once_with(mocked_layer)
    load_kube_config.assert_called_once()
    mocked_core_v1_api.list_namespaced_pod.assert_called_once_with("layer_name")

    mocked_nice_run.assert_called_once_with(
        [
            "kubectl",
            "exec",
            "-n",
            "layer_name",
            "-c",
            "k8s-service",
            "--kubeconfig",
            mocker.ANY,
            "--context",
            mocker.ANY,
            "pod_name",
            "-it",
            "--",
            "bash",
            "-il",
        ]
    )


def test_shell_with_sh(mocker: MockFixture) -> None:
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    mocked_layer_class = mocker.patch("opta.commands.shell.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.name = "layer_name"
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    layer_gen_all = mocker.patch("opta.commands.shell.gen_all")
    set_kube_config = mocker.patch("opta.commands.shell.set_kube_config")
    load_kube_config = mocker.patch("opta.commands.shell.load_opta_kube_config")

    mocked_core_v1_api_class = mocker.patch("opta.commands.shell.CoreV1Api")
    mocked_core_v1_api = mocker.Mock(spec=CoreV1Api)
    mocked_core_v1_api_class.return_value = mocked_core_v1_api

    mocked_v1_pod = mocker.Mock(spec=V1Pod)
    mocked_v1_pod.metadata.name = "pod_name"
    mocked_v1_pod_list = mocker.Mock(spec=V1PodList)
    mocked_v1_pod_list.items = [mocked_v1_pod]
    mocked_core_v1_api.list_namespaced_pod.return_value = mocked_v1_pod_list

    mocked_nice_run = mocker.patch("opta.commands.shell.nice_run")

    runner = CliRunner()
    result = runner.invoke(cli, ["shell", "-t", "sh"])

    assert result.exit_code == 0
    layer_gen_all.assert_called_once_with(mocked_layer)
    set_kube_config.assert_called_once_with(mocked_layer)
    load_kube_config.assert_called_once()
    mocked_core_v1_api.list_namespaced_pod.assert_called_once_with("layer_name")

    mocked_nice_run.assert_called_once_with(
        [
            "kubectl",
            "exec",
            "-n",
            "layer_name",
            "-c",
            "k8s-service",
            "--kubeconfig",
            mocker.ANY,
            "--context",
            mocker.ANY,
            "pod_name",
            "-it",
            "--",
            "sh",
            "-il",
        ]
    )


def test_shell_with_invalid_shell(mocker: MockFixture) -> None:
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    mocked_layer_class = mocker.patch("opta.commands.shell.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.name = "layer_name"
    mocked_layer_class.load_from_yaml.return_value = mocked_layer

    mocked_core_v1_api_class = mocker.patch("opta.commands.shell.CoreV1Api")
    mocked_core_v1_api = mocker.Mock(spec=CoreV1Api)
    mocked_core_v1_api_class.return_value = mocked_core_v1_api

    mocked_v1_pod = mocker.Mock(spec=V1Pod)
    mocked_v1_pod.metadata.name = "pod_name"
    mocked_v1_pod_list = mocker.Mock(spec=V1PodList)
    mocked_v1_pod_list.items = [mocked_v1_pod]
    mocked_core_v1_api.list_namespaced_pod.return_value = mocked_v1_pod_list

    runner = CliRunner()
    result = runner.invoke(cli, ["shell", "-t", "shh"])

    assert result.exit_code == 2
