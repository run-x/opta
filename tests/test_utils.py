from pytest_mock import MockFixture

from opta.utils import exp_backoff


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
