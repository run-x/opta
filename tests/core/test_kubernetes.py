import datetime
from subprocess import CompletedProcess

import pytz
from kubernetes.client import ApiException, CoreV1Api, V1Event, V1EventList, V1Pod
from kubernetes.watch import Watch
from pytest_mock import MockFixture

from opta.core.kubernetes import (
    configure_kubectl,
    tail_module_log,
    tail_namespace_events,
    tail_pod_log,
)
from opta.layer import Layer


class TestKubernetes:
    def test_azure_configure_kubectl(self, mocker: MockFixture) -> None:
        mocked_is_tool = mocker.patch(
            "opta.core.kubernetes.is_tool", side_effect=[True, True]
        )
        layer = mocker.Mock(spec=Layer)
        layer.parent = None
        layer.cloud = "azurerm"
        layer.name = "blah"
        layer.providers = {
            "azurerm": {
                "location": "centralus",
                "tenant_id": "blahbc17-blah-blah-blah-blah291d395b",
                "subscription_id": "blah99ae-blah-blah-blah-blahd2a04788",
            }
        }
        layer.root.return_value = layer
        layer.gen_providers.return_value = {
            "terraform": {
                "backend": {"azurerm": {"resource_group_name": "dummy_resource_group"}}
            },
            "provider": {
                "azurerm": {
                    "location": "centralus",
                    "tenant_id": "blahbc17-blah-blah-blah-blah291d395b",
                    "subscription_id": "blah99ae-blah-blah-blah-blahd2a04788",
                }
            },
        }
        mocked_terraform_output = mocker.patch(
            "opta.core.kubernetes.get_terraform_outputs",
            return_value={"k8s_cluster_name": "mocked_cluster_name"},
        )
        mocked_nice_run = mocker.patch("opta.core.kubernetes.nice_run",)

        configure_kubectl(layer)

        mocked_terraform_output.assert_called_once_with(layer)
        mocked_is_tool.assert_has_calls([mocker.call("kubectl"), mocker.call("az")])
        mocked_nice_run.assert_has_calls(
            [
                mocker.call(
                    [
                        "az",
                        "aks",
                        "get-credentials",
                        "--resource-group",
                        "dummy_resource_group",
                        "--name",
                        "mocked_cluster_name",
                        "--admin",
                        "--overwrite-existing",
                    ],
                    check=True,
                ),
            ]
        )

    def test_configure_kubectl(self, mocker: MockFixture) -> None:
        mocked_is_tool = mocker.patch(
            "opta.core.kubernetes.is_tool", side_effect=[True, True]
        )
        mocked_nice_run = mocker.patch(
            "opta.core.kubernetes.nice_run",
            side_effect=[
                CompletedProcess(
                    None,  # type: ignore
                    0,
                    """{"UserId": "mocked_user_id:jd@runx.dev","Account": "111111111111", "Arn": "mocked_arn"}""".encode(
                        "utf-8"
                    ),
                ),
                CompletedProcess(None, 0, "blah".encode("utf-8")),  # type: ignore
            ],
        )
        layer = mocker.Mock(spec=Layer)
        layer.parent = None
        layer.cloud = "aws"
        layer.name = "blah"
        layer.providers = {"aws": {"region": "us-east-1", "account_id": "111111111111"}}
        layer.root.return_value = layer
        mocked_terraform_output = mocker.patch(
            "opta.core.kubernetes.get_terraform_outputs",
            return_value={"k8s_cluster_name": "mocked_cluster_name"},
        )

        configure_kubectl(layer)

        mocked_terraform_output.assert_called_once_with(layer)
        mocked_is_tool.assert_has_calls([mocker.call("kubectl"), mocker.call("aws")])
        mocked_nice_run.assert_has_calls(
            [
                mocker.call(
                    ["aws", "sts", "get-caller-identity"], check=True, capture_output=True
                ),
                mocker.call(
                    [
                        "aws",
                        "eks",
                        "update-kubeconfig",
                        "--name",
                        "mocked_cluster_name",
                        "--region",
                        "us-east-1",
                    ]
                ),
            ]
        )

    def test_tail_module_log(self, mocker: MockFixture) -> None:
        mocked_load_kube_config = mocker.patch("opta.core.kubernetes.load_kube_config")
        mocked_core_v1_api = mocker.Mock(spec=CoreV1Api)
        mocked_core_v1_api_call = mocker.patch(
            "opta.core.kubernetes.CoreV1Api", return_value=mocked_core_v1_api
        )
        mocked_watch = mocker.Mock(spec=Watch)
        mocked_watch_call = mocker.patch(
            "opta.core.kubernetes.Watch", return_value=mocked_watch
        )
        mocked_is_past_datetime_utc = mocker.patch(
            "opta.core.kubernetes.is_past_datetime_utc", return_value=False
        )
        layer = mocker.Mock(spec=Layer)
        layer.name = "mocked_layer"
        layer.parent = None
        layer.providers = {"aws": {"region": "us-east-1", "account_id": "111111111111"}}
        mocked_pod_1 = mocker.Mock(spec=V1Pod)
        mocked_pod_1.metadata = mocker.Mock()
        mocked_pod_1.metadata.name = "pod1"
        mocked_event_1 = {"object": mocked_pod_1}
        thread_1 = mocker.Mock()
        mocked_pod_2 = mocker.Mock(spec=V1Pod)
        mocked_pod_2.metadata = mocker.Mock()
        mocked_pod_2.metadata.name = "pod2"
        mocked_event_2 = {"object": mocked_pod_2}
        thread_2 = mocker.Mock()
        mocked_watch.stream.return_value = [mocked_event_1, mocked_event_2]

        mocked_thread = mocker.patch(
            "opta.core.kubernetes.Thread", side_effect=[thread_1, thread_2]
        )

        tail_module_log(layer, "mocked_module_name", seconds=3, start_color_idx=2)
        mocked_watch_call.assert_called_once_with()
        mocked_core_v1_api_call.assert_called_once_with()
        mocked_load_kube_config.assert_called_once_with()
        mocked_is_past_datetime_utc.assert_called()
        thread_1.start.assert_called_once_with()
        thread_2.start.assert_called_once_with()
        mocked_thread.assert_has_calls(
            [
                mocker.call(
                    target=tail_pod_log,
                    args=("mocked_layer", mocked_pod_1, 2, 3),
                    daemon=True,
                ),
                mocker.call(
                    target=tail_pod_log,
                    args=("mocked_layer", mocked_pod_2, 3, 3),
                    daemon=True,
                ),
            ]
        )

    def test_tail_pod_log(self, mocker: MockFixture) -> None:
        mocked_core_v1_api = mocker.Mock(spec=CoreV1Api)
        mocked_core_v1_api_call = mocker.patch(
            "opta.core.kubernetes.CoreV1Api", return_value=mocked_core_v1_api
        )
        mocked_watch = mocker.Mock(spec=Watch)
        mocked_watch_call = mocker.patch(
            "opta.core.kubernetes.Watch", return_value=mocked_watch
        )
        mocked_watch.stream.side_effect = [
            "hello_world",
            ApiException(status=400),
            ApiException(status=400),
            ApiException(status=400),
            Exception(),
            ApiException(status=400),
        ]
        mocked_pod = mocker.Mock(spec=V1Pod)
        mocked_pod.metadata = mocker.Mock()
        mocked_pod.metadata.name = "pod1"
        mocked_time = mocker.patch("opta.core.kubernetes.time")

        tail_pod_log("mocked_namespace", mocked_pod, 2, 3)

        mocked_watch_call.assert_called_once_with()
        mocked_core_v1_api_call.assert_called_once_with()
        mocked_time.sleep.assert_has_calls(
            [
                mocker.call(1),
                mocker.call(2),
                mocker.call(4),
                mocker.call(8),
                mocker.call(16),
            ]
        )
        assert mocked_time.sleep.call_count == 5

        # Tailing should not retry upon encountering a 404 API exception.
        mocked_watch.stream.side_effect = [
            "hello_world",
            ApiException(status=400),
            ApiException(status=404),
        ]
        mocked_time = mocker.patch("opta.core.kubernetes.time")
        tail_pod_log("mocked_namespace", mocked_pod, 2, 3)
        assert mocked_time.sleep.call_count == 1

    def test_tail_namespace_events(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.kubernetes.load_kube_config")
        mocked_core_v1_api = mocker.Mock(spec=CoreV1Api)
        mocked_core_v1_api_call = mocker.patch(
            "opta.core.kubernetes.CoreV1Api", return_value=mocked_core_v1_api
        )
        mocked_watch = mocker.Mock(spec=Watch)
        mocked_watch_call = mocker.patch(
            "opta.core.kubernetes.Watch", return_value=mocked_watch
        )
        layer = mocker.Mock(spec=Layer)
        layer.name = "mocked_layer"
        layer.parent = None
        layer.providers = {"aws": {"region": "us-east-1", "account_id": "111111111111"}}
        mocked_old_events = mocker.Mock(spec=V1EventList)
        mocked_event_1 = mocker.Mock(spec=V1Event)
        mocked_event_1.last_timestamp = datetime.datetime.now(
            pytz.utc
        ) - datetime.timedelta(seconds=1)
        mocked_event_1.message = "blah1"
        mocked_event_2 = mocker.Mock(spec=V1Event)
        mocked_event_2.last_timestamp = datetime.datetime.now(
            pytz.utc
        ) - datetime.timedelta(seconds=100)
        mocked_event_2.message = "blah2"
        mocked_event_3 = mocker.Mock(spec=V1Event)
        mocked_event_3.last_timestamp = datetime.datetime.now(
            pytz.utc
        ) - datetime.timedelta(seconds=10)
        mocked_event_3.message = "blah3"
        mocked_old_events.items = [mocked_event_1, mocked_event_2, mocked_event_3]
        mocked_core_v1_api.list_namespaced_event.return_value = mocked_old_events

        mocked_event_4 = mocker.Mock(spec=V1Event)
        mocked_event_4.last_timestamp = datetime.datetime.now(
            pytz.utc
        ) - datetime.timedelta(seconds=100)
        mocked_event_4.message = "blah2"
        mocked_event_5 = mocker.Mock(spec=V1Event)
        mocked_event_5.last_timestamp = datetime.datetime.now(
            pytz.utc
        ) - datetime.timedelta(seconds=10)
        mocked_event_5.message = "blah3"

        mocked_watch.stream.side_effect = [
            [{"object": mocked_event_4}],
            [{"object": mocked_event_5}],
            ApiException(status=400),
            ApiException(status=400),
            ApiException(status=400),
            ApiException(status=400),
            ApiException(status=400),
        ]
        mocked_time = mocker.patch("opta.core.kubernetes.time")

        tail_namespace_events(layer, 2, 3)

        mocked_core_v1_api.list_namespaced_event.assert_called_once_with(
            namespace="mocked_layer"
        )
        mocked_watch_call.assert_called_once_with()
        mocked_core_v1_api_call.assert_called_once_with()
        mocked_time.sleep.assert_has_calls(
            [
                mocker.call(1),
                mocker.call(2),
                mocker.call(4),
                mocker.call(8),
                mocker.call(16),
            ]
        )
