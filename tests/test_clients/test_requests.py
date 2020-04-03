import logging
from datetime import datetime

import requests_mock
from freezegun import freeze_time
from unittest.mock import MagicMock, call

import pytest
import requests

from nephthys.clients.requests import (
    catch_logger_exception,
    decorate_log_request,
    decorate_log_response,
    Session)
from nephthys.filters.requests import BODY_NOT_LOGGABLE


@pytest.fixture
def m():
    with requests_mock.Mocker() as m:
        yield m


def test_exception_catcher_decorator(caplog):
    caplog.set_level(logging.DEBUG, logger="requests_in")

    def on_my_funct():
        raise Exception()

    catch_logger_exception(on_my_funct)()

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelno == logging.ERROR
    assert record.msg == "Failed to log"
    assert record.exc_info is not None


def test_decorate_log_request_headers():
    log_record = MagicMock()
    test_headers = {"key1": "value1", "key2": "value2"}
    request = MagicMock(url="https://ovalmoney.com", headers=test_headers)
    decorate_log_request(log_record, request)
    for name, value in test_headers.items():
        expected = call(name, value)
        assert expected in log_record.add_request_header.call_args_list


def test_decorate_log_request_querystring():
    log_record = MagicMock()
    name, value = "query", "var"
    request = MagicMock(url=f"https://ovalmoney.com?{name}={value}")
    request.headers = None
    decorate_log_request(log_record, request)
    expected = call(name, [value])
    assert expected in log_record.add_request_querystring.call_args_list


def test_decorate_log_request_body():
    log_record = MagicMock()
    request = MagicMock(url=f"https://ovalmoney.com")
    body = MagicMock()
    body.decode.return_value = "return"
    request.body = body
    decorate_log_request(log_record, request)
    assert log_record.request_body == "return"
    body.decode.assert_called_with("UTF-8", errors="strict")


def test_decorate_log_request_body_raises():
    log_record = MagicMock()
    body = MagicMock()
    body.decode.side_effect = UnicodeDecodeError("bla", bytes(0), 0, 1, "bla")
    request = MagicMock(url=f"https://ovalmoney.com", body=body)
    decorate_log_request(log_record, request)
    assert log_record.request_body == "<RAW Data>"
    body.decode.assert_called_with("UTF-8", errors="strict")


def test_decorate_log_response_headers():
    log_record = MagicMock()
    test_headers = {"key1": "value1", "key2": "value2"}
    response = MagicMock(url="https://ovalmoney.com", headers=test_headers)
    decorate_log_response(log_record, response)
    for name, value in test_headers.items():
        expected = call(name, value)
        assert expected in log_record.add_response_header.call_args_list


@pytest.mark.parametrize(
    "encoding,expected_encoding", [(None, "utf-8"), ("utf-8", "utf-8")]
)
def test_decorate_log_response_content(encoding, expected_encoding):
    log_record = MagicMock()
    content = MagicMock()
    content.decode.return_value = "test"
    response = MagicMock(
        url="https://ovalmoney.com", headers=None, encoding=encoding, content=content
    )
    decorate_log_response(log_record, response)
    content.decode.assert_called_with(expected_encoding, errors="strict")
    assert log_record.response_body == "test"


@pytest.mark.parametrize(
    "exception,encoding,expected_encoding",
    [
        (TypeError, None, "utf-8"),
        (UnicodeDecodeError, None, "utf-8"),
        (LookupError, "UtF8", "UtF8"),
    ],
)
def test_decorate_log_response_content_raises(exception, encoding, expected_encoding):
    log_record = MagicMock()
    content = MagicMock()
    content.decode.side_effect = exception
    response = MagicMock(
        url="https://ovalmoney.com", headers=None, encoding=encoding, content=content
    )
    decorate_log_response(log_record, response)
    content.decode.assert_called_with(expected_encoding, errors="strict")
    assert log_record.response_body == "<RAW Data>"


def test_send_log_record(caplog, m):
    caplog.set_level(logging.INFO)
    m.get("https://ovalmoney.com/user", status_code=200)

    s = Session()
    s._logger.info = MagicMock()
    s.get("https://ovalmoney.com/user")

    assert s._logger.info.called


def test_send_log_record_exception(caplog, m):
    caplog.set_level(logging.INFO)
    m.get("https://ovalmoney.com/user", exc=requests.exceptions.ConnectTimeout)

    s = Session()
    s._logger.exception = MagicMock()
    with pytest.raises(requests.exceptions.ConnectTimeout):
        s.get("https://ovalmoney.com/user")

    assert s._logger.exception.called


def test_raw_data_reponse_body_log(caplog, m):
    caplog.set_level(logging.INFO)
    m.get(
        "https://ovalmoney.com/raw_data",
        headers={"Content-Type": "video"},
        content=b"\xFF\x8F",
    )

    s = Session()
    s.get("https://ovalmoney.com/raw_data")

    log_rec = [rec for rec in caplog.records][0]

    assert log_rec.msg["response"]["body"] == BODY_NOT_LOGGABLE.format(
        log_rec.msg["response"]["header"]["Content-Type"]
    )


def test_raw_data_request_body_log(caplog, m):
    caplog.set_level(logging.INFO)
    m.post("https://ovalmoney.com/raw_data")

    s = Session()
    s.post("https://ovalmoney.com/raw_data", headers={"Content-Type": "video"}, data=b"\xFF\x8F")

    log_rec = [rec for rec in caplog.records][0]

    assert log_rec.msg["request"]["body"] == BODY_NOT_LOGGABLE.format(
        log_rec.msg["request"]["header"]["Content-Type"]
    )


def test_text_reponse_body_log(caplog, m):
    caplog.set_level(logging.INFO)
    m.get(
        "https://ovalmoney.com/text_data",
        headers={"Content-Type": "text/plain"},
        text="Response",
    )

    s = Session()
    s.get("https://ovalmoney.com/text_data")

    log_rec = [rec for rec in caplog.records][0]

    assert log_rec.msg["response"]["body"] == "Response"


def test_form_data_request_body_log(caplog, m):
    caplog.set_level(logging.INFO)
    m.post("https://ovalmoney.com/form_data")

    s = Session()
    s.post("https://ovalmoney.com/form_data", data={"key": "value", "key2": "value2"})

    log_rec = [rec for rec in caplog.records][0]

    assert log_rec.msg["request"]["body"] == "key=value&key2=value2"


def test_session_fail_http(m):
    m.get("https://ovalmoney.com/user", exc=requests.exceptions.ConnectTimeout)

    s = Session()
    with pytest.raises(requests.exceptions.ConnectTimeout):
        s.get("https://ovalmoney.com/user")


def test_session_fail_http_log(caplog, m):
    caplog.set_level(logging.INFO)
    m.get("https://ovalmoney.com/user", exc=requests.exceptions.ConnectTimeout)

    s = Session()
    with pytest.raises(requests.exceptions.ConnectTimeout):
        s.get("https://ovalmoney.com/user")

    log_rec = [rec for rec in caplog.records][0]

    assert isinstance(log_rec.exc_info[1], requests.exceptions.ConnectTimeout)
    log = log_rec.msg
    assert log["request"]["method"] == "GET"
    assert log["request"]["url"] == "https://ovalmoney.com/user"
    assert log["request"]["path"] == "/user"
    assert log["request"]["host"] == "ovalmoney.com"


def test_session_success(caplog, m):
    caplog.set_level(logging.INFO)
    m.get(
        "https://ovalmoney.com/user?key1=value1&key2=value2&key2=value3",
        json={"test": True},
        headers={"Content-Type": "application/json"},
        status_code=200,
    )

    s = Session()
    response = s.get("https://ovalmoney.com/user", params={"key1": "value1", "key2": ["value2", "value3"]})

    assert response.headers
    assert response.status_code == 200
    assert response.json() == {"test": True}


def test_session_success_log(caplog, m):
    caplog.set_level(logging.INFO)
    m.get(
        "https://ovalmoney.com/user?key1=value1&key2=value2&key2=value3",
        json={"test": True},
        headers={"Content-Type": "application/json"},
        status_code=200,
    )

    with freeze_time(datetime.utcnow()):
        s = Session(log_tag="test")
        s.get("https://ovalmoney.com/user", params={"key1": "value1", "key2": ["value2", "value3"]})
        now = datetime.utcnow().timestamp()

    log = [rec.msg for rec in caplog.records][0]

    assert log["extra_tags"] == ["test", "requests_out"]

    assert log["request"]["start"] == now
    assert log["request"]["end"] == now
    assert log["request"]["time"] == 0.0

    assert log["request"]["method"] == "GET"
    assert (
            log["request"]["url"]
            == "https://ovalmoney.com/user?key1=value1&key2=value2&key2=value3"
    )
    assert log["request"]["path"] == "/user"
    assert log["request"]["host"] == "ovalmoney.com"
    assert log["request"]["query"] == {"key1": "value1", "key2": "value2,value3"}

    assert log["response"]["body"] == '{"test": true}'
    assert log["response"]["status_code"] == 200
