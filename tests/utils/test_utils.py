import json
import os

import click
import pytest
from pytest_mock import MockFixture

from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import (
    SensitiveFormatter,
    alternate_yaml_extension,
    check_opta_file_exists,
    exp_backoff,
)


def test_sensitive_formatter_on_aws_yaml() -> None:
    layer = Layer.load_from_yaml(
        os.path.join(
            os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
        ),
        None,
    )
    original_spec = layer.original_spec
    formatted_spec = SensitiveFormatter.filter(original_spec)
    assert "111111111111" not in formatted_spec


def test_sensitive_formatter_on_gcp_yaml() -> None:
    layer = Layer.load_from_yaml(
        os.path.join(
            os.getcwd(), "tests", "fixtures", "dummy_data", "gcp_dummy_config_parent.yaml"
        ),
        None,
    )
    original_spec = layer.original_spec
    formatted_spec = SensitiveFormatter.filter(original_spec)
    assert "my-gcp-project" not in formatted_spec


def test_sensitive_formatter_on_aws_tfplan() -> None:
    path = os.path.join(
        os.getcwd(), "tests", "fixtures", "sample_tf_plan_files", "aws_tfplan"
    )
    with open(path) as f:
        tfplan_text = f.read()
    formatted_tfplan = SensitiveFormatter.filter(tfplan_text)
    assert "111111111111" not in formatted_tfplan
    assert json.loads(formatted_tfplan)


def test_sensitive_formatter_on_gcp_tfplan() -> None:
    path = os.path.join(
        os.getcwd(), "tests", "fixtures", "sample_tf_plan_files", "gcp_tfplan"
    )
    with open(path) as f:
        tfplan_text = f.read()
    formatted_tfplan = SensitiveFormatter.filter(tfplan_text)
    assert "my-gcp-project" not in formatted_tfplan
    assert json.loads(formatted_tfplan)


def test_exp_backoff(mocker: MockFixture) -> None:
    # Sleep should be exponential for each iteration
    mocked_sleep = mocker.patch("opta.utils.sleep")
    retries = 3
    for _ in exp_backoff(num_tries=retries):
        pass
    raw_call_args = mocked_sleep.call_args_list
    sleep_param_history = [arg[0][0] for arg in raw_call_args]
    assert sleep_param_history == [2, 4, 16]

    # Sleep should not be called if body succeeded and exited.
    mocked_sleep = mocker.patch("opta.utils.sleep")
    for _ in exp_backoff(num_tries=retries):
        break
    assert mocked_sleep.call_count == 0


def test_check_opta_file_exists_file_exists(mocker: MockFixture) -> None:
    mock_config_path = "mock_config_path"
    mock_os_path_exists = mocker.patch("opta.utils.os.path.exists", return_value=True)
    mock_click_prompt = mocker.patch("opta.utils.click.prompt")
    mock_system_exit = mocker.patch("opta.utils.sys.exit")

    config_path = check_opta_file_exists(mock_config_path)

    assert config_path == mock_config_path
    mock_os_path_exists.assert_called_once_with(mock_config_path)
    mock_click_prompt.assert_not_called()
    mock_system_exit.assert_not_called()


def test_check_opta_file_exists_file_does_not_exists_user_input(
    mocker: MockFixture,
) -> None:
    mock_config_path = "mock_config_path"
    mock_user_config_path = "mock_user_config_path"
    mock_os_path_exists = mocker.patch(
        "opta.utils.os.path.exists", side_effect=[False, True]
    )
    mock_click_prompt = mocker.patch(
        "opta.utils.click.prompt", return_value=mock_user_config_path
    )
    mock_system_exit = mocker.patch("opta.utils.sys.exit")

    config_path = check_opta_file_exists(mock_config_path)

    assert config_path == mock_user_config_path
    mock_os_path_exists.assert_has_calls(
        [mocker.call(mock_config_path), mocker.call(mock_user_config_path)]
    )
    mock_click_prompt.assert_called_once_with(
        "Enter a Configuration Path (Empty String will exit)",
        default="",
        type=click.STRING,
        show_default=False,
    )
    mock_system_exit.assert_not_called()


def test_check_opta_file_exists_file_does_not_exists_no_user_input(
    mocker: MockFixture,
) -> None:
    mock_config_path = "mock_config_path"
    mock_no_user_config_path = ""
    mock_os_path_exists = mocker.patch(
        "opta.utils.os.path.exists", side_effect=[False, False]
    )
    mock_click_prompt = mocker.patch(
        "opta.utils.click.prompt", return_value=mock_no_user_config_path
    )
    mock_system_exit = mocker.patch("opta.utils.sys.exit")

    config_path = check_opta_file_exists(mock_config_path)

    assert config_path == mock_no_user_config_path
    mock_os_path_exists.assert_called_once_with(mock_config_path)
    mock_click_prompt.assert_called_once_with(
        "Enter a Configuration Path (Empty String will exit)",
        default="",
        type=click.STRING,
        show_default=False,
    )
    mock_system_exit.assert_called_once_with(0)


def test_check_opta_file_exists_file_does_not_exists_invalid_user_input(
    mocker: MockFixture,
) -> None:
    mock_config_path = "mock_config_path"
    mock_invalid_user_config_path = "mock_invalid_user_config_path"
    mock_os_path_exists = mocker.patch(
        "opta.utils.os.path.exists", side_effect=[False, False]
    )
    mock_click_prompt = mocker.patch(
        "opta.utils.click.prompt", return_value=mock_invalid_user_config_path
    )
    mock_system_exit = mocker.patch("opta.utils.sys.exit")

    with pytest.raises(UserErrors):
        _ = check_opta_file_exists(mock_config_path)

    mock_os_path_exists.assert_has_calls(
        [mocker.call(mock_config_path), mocker.call(mock_invalid_user_config_path)]
    )
    mock_click_prompt.assert_called_once_with(
        "Enter a Configuration Path (Empty String will exit)",
        default="",
        type=click.STRING,
        show_default=False,
    )
    mock_system_exit.assert_not_called()


def test_alternate_yaml_extension() -> None:
    assert alternate_yaml_extension("opta.yaml") == ("opta.yml", True)
    assert alternate_yaml_extension("opta.yml") == ("opta.yaml", True)
    assert alternate_yaml_extension("opta.YML") == ("opta.yaml", True)
    assert alternate_yaml_extension("path/opta.yml") == ("path/opta.yaml", True)
    assert alternate_yaml_extension("path/config") == ("path/config", False)
