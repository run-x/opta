# type: ignore
import os

import pytest
from pytest_mock import MockFixture

from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.module_processors.runx import OPTA_DOMAIN, RunxProcessor


class TestRunxProcessor:
    def test_init_no_api_key(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        runx_module = layer.get_module("runx", 7)
        with pytest.raises(UserErrors):
            RunxProcessor(runx_module, layer)

    def test_init_api_key(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        os.environ["OPTA_API_KEY"] = "blah"
        runx_module = layer.get_module("runx", 7)
        RunxProcessor(runx_module, layer)

    def test_process(self, mocker: MockFixture):
        mocked_fetch_jwt = mocker.patch(
            "opta.module_processors.runx.RunxProcessor.fetch_jwt"
        )
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        os.environ["OPTA_API_KEY"] = "blah"
        runx_module = layer.get_module("runx", 7)
        RunxProcessor(runx_module, layer).process(7)
        mocked_fetch_jwt.assert_called_once_with()

    def test_post_hook(self, mocker: MockFixture):
        mocked_fetch_jwt = mocker.patch(
            "opta.module_processors.runx.RunxProcessor.fetch_jwt"
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
        os.environ["OPTA_API_KEY"] = "blah"
        runx_module = layer.get_module("runx", 7)

        mocked_request = mocker.patch("opta.module_processors.runx.requests")
        mocked_response = mocker.Mock()
        mocked_request.post.return_value = mocked_response
        mocked_response.status_code = 201

        RunxProcessor(runx_module, layer).post_hook(7, None)

        mocked_request.post.assert_called_once_with(
            f"https://{OPTA_DOMAIN}/config/services",
            json=mocker.ANY,
            headers={"opta": "blah"},
        )

    def test_fetch_jwt(self, mocker: MockFixture):
        mocked_request = mocker.patch("opta.module_processors.runx.requests")
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
        os.environ["OPTA_API_KEY"] = "blah"
        runx_module = layer.get_module("runx", 7)
        assert RunxProcessor(runx_module, layer).fetch_jwt() == ({"a": "b"}, "baloney")
        mocked_request.post.assert_called_once_with(
            f"https://{OPTA_DOMAIN}/user/apikeys/validate", json={"api_key": "blah"}
        )

    def test_fetch_jwt_404(self, mocker: MockFixture):
        mocked_request = mocker.patch("opta.module_processors.runx.requests")
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
        os.environ["OPTA_API_KEY"] = "blah"
        runx_module = layer.get_module("runx", 7)
        with pytest.raises(UserErrors):
            RunxProcessor(runx_module, layer).fetch_jwt()

    def test_fetch_jwt_500(self, mocker: MockFixture):
        mocked_request = mocker.patch("opta.module_processors.runx.requests")
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
        os.environ["OPTA_API_KEY"] = "blah"
        runx_module = layer.get_module("runx", 7)
        with pytest.raises(Exception):
            RunxProcessor(runx_module, layer).fetch_jwt()
