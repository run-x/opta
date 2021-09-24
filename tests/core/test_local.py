import sys
from unittest.mock import MagicMock, Mock

from pytest import fixture
from pytest_mock import MockFixture

from opta.layer import Layer

sys.modules["json.load"] = MagicMock(return_value={"a": 1})
from opta.core.local import Local


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
    def test_get_remote_config_happypath(self, local_layer: Mock) -> None:
        local = Local(local_layer)
        assert local.get_remote_config() == {"a": 1}
