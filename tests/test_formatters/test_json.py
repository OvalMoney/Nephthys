import json
import sys
from logging import LogRecord

import pytest

from nephthys.formatters.json import JSONRenderer, JSONFormatter


@pytest.fixture
def msg():
    return {"test": "test"}


def serializable_obj():
    return


def test_renderer():
    renderer = JSONRenderer()
    assert renderer({"key": 2 + 1j}) == '{"key":"(2+1j)"}'
    assert renderer({"test": "test"}) == '{"test":"test"}'
    assert renderer({"b": "test", "a": "test"}) != '{"a":"test","b": "test"}'


def test_renderer_sort():
    renderer = JSONRenderer(sort_keys=True)
    assert renderer({"b": "test", "a": "test"}) == '{"a":"test","b":"test"}'


def test_renderer_indent():
    renderer = JSONRenderer(indent=1)
    assert renderer({"test": "test"}) == '{\n "test": "test"\n}'


def test_renderer_default():
    renderer = JSONRenderer()
    assert renderer("test") == '"test"'


def test_defaults():
    formatter = JSONFormatter(fmt="$(message)s")

    assert isinstance(formatter._renderer, JSONRenderer)
    assert formatter._required_fields == ["message"]


def test_not_a_dict():
    formatter = JSONFormatter()
    log = LogRecord("test", 20, "/app/module", 1, "My message", [], None)
    out = formatter.format(log)

    assert out == '{"message":"My message"}'


def test_default(msg):
    formatter = JSONFormatter()
    log = LogRecord("test", 20, "/app/module", 1, msg, [], None)
    out = formatter.format(log)

    assert out == '{"message":null,"test":"test"}'


def test_required_parameters(msg):
    formatter = JSONFormatter(fmt="$(name)s $(levelno)s $(pathname)s $(lineno)s")
    log = LogRecord("test", 20, "/app/module", 1, msg, [], None)
    out = formatter.format(log)

    assert (
        out
        == '{"name":"test","levelno":20,"pathname":"/app/module","lineno":1,"test":"test"}'
    )


def test_exception(msg):
    formatter = JSONFormatter()

    try:
        raise Exception
    except Exception:
        exc_info = sys.exc_info()

        log = LogRecord(
            "test", 20, "/app/module", 1, msg, [], exc_info, sinfo="Stack Informations"
        )
        out = formatter.format(log)
        out_dict = json.loads(out)

        assert out_dict["exc_info"] == formatter.formatException(exc_info)
        assert out_dict["stack_info"] == "Stack Informations"
        assert out_dict["test"] == "test"
