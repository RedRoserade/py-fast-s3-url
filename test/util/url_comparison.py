from urllib.parse import urlparse, parse_qs


def assert_urls_match(actual: str, expected: str) -> None:
    """
    Check that the URLs match, by comparing their components.
    Query string parameters are compared out-of-order.
    """

    parsed_actual = urlparse(actual)
    parsed_expected = urlparse(expected)

    assert parsed_actual.scheme == parsed_expected.scheme
    assert parsed_actual.netloc == parsed_expected.netloc
    assert parsed_actual.path == parsed_expected.path
    assert parse_qs(parsed_actual.params) == parse_qs(parsed_expected.params)
