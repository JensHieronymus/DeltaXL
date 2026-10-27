from deltaxl import __version__


def test_version_string():
    assert isinstance(__version__, str)
    assert __version__.count(".") == 2
