import rapidjson
import pytest

from nephthys import RequestLogRecord, LogRecord
from nephthys.filters.requests import HeaderFilter, BodyTypeFilter, JsonBodyFilter, QueryStringFilter
from nephthys.filters.requests import (
    RequestType,
    QS_FILTERED,
    HEADER_FILTERED,
    BODY_NOT_LOGGABLE,
    JSON_BODY_FILTERED,
)


def rec_generator():
    return LogRecord(extra_tags=["my_tag"])


def req_rec_generator(
    request_headers=None, response_headers=None, request_body=None, response_body=None, qs=None
):
    req_rec = RequestLogRecord()

    for name, value in request_headers or []:
        req_rec.add_request_header(name, value)
    for name, value in response_headers or []:
        req_rec.add_response_header(name, value)

    for name, value in qs or []:
        req_rec.add_request_querystring(name, value)

    req_rec.request_body = request_body
    req_rec.response_body = response_body

    return req_rec


@pytest.mark.parametrize(
    "filters,in_record,out_record",
    [
        (
            ["QSFiltered", "QSfiltered2"],
            req_rec_generator(
                qs=[
                    ("QSFiltered", "value1"),
                    ("QSfiltered", "value2"),
                    ("QSNotFiltered", "value3"),
                    ("QSfiltered2", "value4"),
                ],
            ),
            req_rec_generator(
                qs=[
                    ("QSFiltered", QS_FILTERED),
                    ("QSfiltered", "value2"),
                    ("QSNotFiltered", "value3"),
                    ("QSfiltered2", QS_FILTERED),
                ],
            ),
        ),
        (
            [],
            req_rec_generator(
                qs=[
                    ("QSFiltered", "value1"),
                    ("QSfiltered", "value2"),
                    ("QSNotFiltered", "value3"),
                    ("QSfiltered2", "value4"),
                ],
            ),
            req_rec_generator(
                qs=[
                    ("QSFiltered", "value1"),
                    ("QSfiltered", "value2"),
                    ("QSNotFiltered", "value3"),
                    ("QSfiltered2", "value4"),
                ],
            ),
        ),
        (["QSFiltered"], rec_generator(), rec_generator()),
    ],
)
def test_qs_filter(filters, in_record, out_record):
    qs_filter = QueryStringFilter(filters)

    qs_filter.filter(in_record)

    assert in_record.asdict() == out_record.asdict()


@pytest.mark.parametrize(
    "filters,req_type,in_record,out_record",
    [
        (
            ["X-Filter-me"],
            RequestType.REQUEST,
            req_rec_generator(
                request_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
                response_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
            ),
            req_rec_generator(
                request_headers=[
                    ("X-Filter-Me", HEADER_FILTERED),
                    ("X-Not-Filter-Me", "value2"),
                ],
                response_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
            ),
        ),
        (
            ["X-Filter-Me"],
            RequestType.RESPONSE,
            req_rec_generator(
                request_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
                response_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
            ),
            req_rec_generator(
                request_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
                response_headers=[
                    ("X-Filter-Me", HEADER_FILTERED),
                    ("X-Not-Filter-Me", "value2"),
                ],
            ),
        ),
        (
            ["X-Filter-Me"],
            RequestType.ALL,
            req_rec_generator(
                request_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
                response_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
            ),
            req_rec_generator(
                request_headers=[
                    ("X-Filter-Me", HEADER_FILTERED),
                    ("X-Not-Filter-Me", "value2"),
                ],
                response_headers=[
                    ("X-Filter-Me", HEADER_FILTERED),
                    ("X-Not-Filter-Me", "value2"),
                ],
            ),
        ),
        (
            ["X-Filter-Me"],
            RequestType.ALL,
            req_rec_generator(
                request_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ]
            ),
            req_rec_generator(
                request_headers=[
                    ("X-Filter-Me", HEADER_FILTERED),
                    ("X-Not-Filter-Me", "value2"),
                ]
            ),
        ),
        (
            [],
            RequestType.ALL,
            req_rec_generator(
                request_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
                response_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
            ),
            req_rec_generator(
                request_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
                response_headers=[
                    ("X-Filter-Me", "value1"),
                    ("X-Not-Filter-Me", "value2"),
                ],
            ),
        ),
        (["X-Filter-Me"], RequestType.ALL, rec_generator(), rec_generator()),
    ],
)
def test_header_filter(filters, req_type, in_record, out_record):
    head_filter = HeaderFilter(filters, req_type)

    head_filter.filter(in_record)

    assert in_record.asdict() == out_record.asdict()


@pytest.mark.parametrize(
    "filters,req_type,in_record,out_record",
    [
        (
            None,
            RequestType.REQUEST,
            req_rec_generator(
                request_headers=[("Content-Type", "multipart/form-data")],
                response_headers=[("Content-Type", "image/jpeg")],
                request_body="Filter-Me",
                response_body="Not-Filter-Me",
            ),
            req_rec_generator(
                request_headers=[("Content-Type", "multipart/form-data")],
                response_headers=[("Content-Type", "image/jpeg")],
                request_body=BODY_NOT_LOGGABLE.format("multipart/form-data"),
                response_body="Not-Filter-Me",
            ),
        ),
        (
            None,
            RequestType.RESPONSE,
            req_rec_generator(
                request_headers=[("Content-Type", "image/jpeg")],
                response_headers=[("Content-Type", "multipart/form-data")],
                request_body="Not-Filter-Me",
                response_body="Filter-Me",
            ),
            req_rec_generator(
                request_headers=[("Content-Type", "image/jpeg")],
                response_headers=[("Content-Type", "multipart/form-data")],
                request_body="Not-Filter-Me",
                response_body=BODY_NOT_LOGGABLE.format("multipart/form-data"),
            ),
        ),
        (
            None,
            RequestType.ALL,
            req_rec_generator(
                request_headers=[("Content-Type", "multipart/form-data")],
                response_headers=[("Content-Type", "image/jpeg")],
                request_body="Filter-Me",
                response_body="Filter-Me",
            ),
            req_rec_generator(
                request_headers=[("Content-Type", "multipart/form-data")],
                response_headers=[("Content-Type", "image/jpeg")],
                request_body=BODY_NOT_LOGGABLE.format("multipart/form-data"),
                response_body=BODY_NOT_LOGGABLE.format("image/jpeg"),
            ),
        ),
        (
            ["application/json"],
            RequestType.ALL,
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                response_headers=[("Content-Type", "text/plain")],
                request_body="Not-Filter-Me",
                response_body="Filter-Me",
            ),
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                response_headers=[("Content-Type", "text/plain")],
                request_body="Not-Filter-Me",
                response_body=BODY_NOT_LOGGABLE.format("text/plain"),
            ),
        ),
        (
            ["application/json"],
            RequestType.ALL,
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                request_body="Not-Filter-Me",
            ),
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                request_body="Not-Filter-Me",
            ),
        ),
        (["application/json"], RequestType.ALL, rec_generator(), rec_generator()),
    ],
)
def test_body_type_filter(filters, req_type, in_record, out_record):
    head_filter = BodyTypeFilter(filters, req_type)

    head_filter.filter(in_record)

    assert in_record.asdict() == out_record.asdict()


@pytest.mark.parametrize(
    "filters,req_type,in_record,out_record",
    [
        (
            {"key": True},
            RequestType.REQUEST,
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                response_headers=[("Content-Type", "application/json")],
                request_body=rapidjson.dumps(
                    {"key": "Filter-Me", "key2": "Not-Filter-Me"}
                ),
                response_body=rapidjson.dumps({"key": "Not-filter-Me"}),
            ),
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                response_headers=[("Content-Type", "application/json")],
                request_body=rapidjson.dumps(
                    {"key": JSON_BODY_FILTERED, "key2": "Not-Filter-Me"}
                ),
                response_body=rapidjson.dumps({"key": "Not-filter-Me"}),
            ),
        ),
        (
            {"key": True},
            RequestType.RESPONSE,
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                response_headers=[("Content-Type", "application/json")],
                request_body=rapidjson.dumps({"key": "Not-filter-Me"}),
                response_body=rapidjson.dumps(
                    {"key": "Filter-Me", "key2": "Not-Filter-Me"}
                ),
            ),
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                response_headers=[("Content-Type", "application/json")],
                request_body=rapidjson.dumps({"key": "Not-filter-Me"}),
                response_body=rapidjson.dumps(
                    {"key": JSON_BODY_FILTERED, "key2": "Not-Filter-Me"}
                ),
            ),
        ),
        (
            {"key": {"key": True}},
            RequestType.ALL,
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                response_headers=[("Content-Type", "application/json")],
                request_body=rapidjson.dumps({"key": {"key": "Filter-Me"}}),
                response_body=rapidjson.dumps(
                    {"key": {"key": "Filter-Me"}, "key2": "Not-Filter-Me"}
                ),
            ),
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                response_headers=[("Content-Type", "application/json")],
                request_body=rapidjson.dumps({"key": {"key": JSON_BODY_FILTERED}}),
                response_body=rapidjson.dumps(
                    {"key": {"key": JSON_BODY_FILTERED}, "key2": "Not-Filter-Me"}
                ),
            ),
        ),
        (
            {"key": {"key": True}},
            RequestType.ALL,
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                response_headers=[("Content-Type", "application/json")],
                request_body=rapidjson.dumps({"key": "Not-Filter-Me"}),
                response_body=rapidjson.dumps({"key2": "Not-Filter-Me"}),
            ),
            req_rec_generator(
                request_headers=[("Content-Type", "application/json")],
                response_headers=[("Content-Type", "application/json")],
                request_body=rapidjson.dumps({"key": "Not-Filter-Me"}),
                response_body=rapidjson.dumps({"key2": "Not-Filter-Me"}),
            ),
        ),
        (
            {"key": {"key": True}},
            RequestType.ALL,
            req_rec_generator(
                request_headers=[("Content-Type", "text/plain")],
                response_headers=[("Content-Type", "application/json")],
                request_body="Not-Filter-Me",
                response_body=rapidjson.dumps({"key2": "Not-Filter-Me"}),
            ),
            req_rec_generator(
                request_headers=[("Content-Type", "text/plain")],
                response_headers=[("Content-Type", "application/json")],
                request_body="Not-Filter-Me",
                response_body=rapidjson.dumps({"key2": "Not-Filter-Me"}),
            ),
        ),
        ({"key": {"key": True}}, RequestType.ALL, rec_generator(), rec_generator()),
    ],
)
def test_json_body_filter(filters, req_type, in_record, out_record):
    head_filter = JsonBodyFilter(filters, req_type)

    head_filter.filter(in_record)

    assert in_record.asdict() == out_record.asdict()
