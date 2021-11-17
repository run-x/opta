from opta.json_schema import check_json_schema


def test_returns_without_error() -> None:
    check_json_schema()
