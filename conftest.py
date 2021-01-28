def pytest_configure(config) -> None:  # type: ignore
    import sys

    sys._called_from_test = True  # type: ignore


def pytest_unconfigure(config) -> None:  # type: ignore
    import sys  # This was missing from the manual

    del sys._called_from_test  # type: ignore
