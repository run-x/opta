from unittest.mock import Mock, mock_open, patch

from pytest import fixture
from pytest_mock import MockFixture

from opta.core.local import Local
from opta.layer import Layer


@fixture()
def local_layer() -> Mock:
    layer = Mock(spec=Layer)
    layer.parent = None
    layer.cloud = "local"
    layer.name = "testlayer"
    layer.path = "~/.opta/local/tfstate"
    layer.org_name = "testorg"
    layer.providers = {"local": {}}
    layer.root.return_value = layer
    layer.gen_providers.return_value = {
        "terraform": {"backend": {"local": {}}},
        "provider": {"local": {}},
    }
    return layer


class TestLocal:
    def test_get_remote_config_happypath(self, mocker: MockFixture, local_layer: Mock) -> None:
        mocker.patch("json.load", return_value="{'a': 1}")
        assert Local(local_layer).get_remote_config() == {"a": 1}

