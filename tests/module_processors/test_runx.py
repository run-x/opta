# type: ignore
import os

import pytest
from pytest_mock import MockFixture

from opta.exceptions import UserErrors
from opta.layer import Layer
from modules.runx.runx import OPTA_DOMAIN, RunxProcessor


class TestRunxProcessor:
    def test_process(self, mocker: MockFixture):
        mocked_fetch_secret = mocker.patch(
            "modules.runx.runx.RunxProcessor.fetch_secret"
        )
        mocked_fetch_secret.return_value = None
        mocked_set_secret = mocker.patch(
            "modules.runx.runx.RunxProcessor.set_secret"
        )
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        runx_module = layer.parent.get_module("runx", 7)
        RunxProcessor(runx_module, layer).process(7)
        mocked_fetch_secret.assert_called_once_with()
        mocked_set_secret.assert_called_once_with()

    def test_post_hook(self, mocker: MockFixture):
        mocked_fetch_secret = mocker.patch(
            "modules.runx.runx.RunxProcessor.fetch_secret"
        )
        mocked_fetch_jwt = mocker.patch(
            "modules.runx.runx.RunxProcessor.fetch_jwt"
        )
        mocked_fetch_jwt.return_value = ({"org_id": "dummy_or"}, "blah")
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        runx_module = layer.parent.get_module("runx", 7)

        mocked_request = mocker.patch("modules.runx.runx.requests")
        mocked_response = mocker.Mock()
        mocked_request.post.return_value = mocked_response
        mocked_response.status_code = 201

        RunxProcessor(runx_module, layer).post_hook(7, None)

        mocked_request.post.assert_called_once_with(
            f"https://{OPTA_DOMAIN}/config/services",
            json=mocker.ANY,
            headers={"opta": "blah"},
        )
        mocked_fetch_secret.assert_called_once_with()

    def test_fetch_jwt(self, mocker: MockFixture):
        mocked_request = mocker.patch("modules.runx.runx.requests")
        mocked_response = mocker.Mock()
        mocked_request.post.return_value = mocked_response
        mocked_response.status_code = 200
        mocked_response.headers = {"opta": "baloney"}
        mocked_response.json.return_value = {"a": "b"}
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        runx_module = layer.parent.get_module("runx", 7)
        assert RunxProcessor(runx_module, layer).fetch_jwt("blah") == (
            {"a": "b"},
            "baloney",
        )
        mocked_request.post.assert_called_once_with(
            f"https://{OPTA_DOMAIN}/user/apikeys/validate", json={"api_key": "blah"}
        )

    def test_fetch_jwt_404(self, mocker: MockFixture):
        mocked_request = mocker.patch("modules.runx.runx.requests")
        mocked_response = mocker.Mock()
        mocked_request.post.return_value = mocked_response
        mocked_response.status_code = 404
        mocked_response.json.return_value = {"message": "blah"}
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        runx_module = layer.parent.get_module("runx", 7)
        with pytest.raises(UserErrors):
            RunxProcessor(runx_module, layer).fetch_jwt("blah")

    def test_fetch_jwt_500(self, mocker: MockFixture):
        mocked_request = mocker.patch("modules.runx.runx.requests")
        mocked_response = mocker.Mock()
        mocked_request.post.return_value = mocked_response
        mocked_response.status_code = 500
        mocked_response.json.return_value = {"message": "blah"}
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        runx_module = layer.parent.get_module("runx", 7)
        with pytest.raises(Exception):
            RunxProcessor(runx_module, layer).fetch_jwt("blah")
