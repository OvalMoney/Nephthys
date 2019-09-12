import rapidjson
from enum import Enum

from .. import RequestLogRecord


class RequestType(Enum):
    ALL = 1
    REQUEST = 2
    RESPONSE = 3


HEADER_FILTERED = "<filtered>"


def filter_headers(filters, headers):
    for hf in filters:
        hft = hf.title()
        if hft in headers:
            headers[hft] = HEADER_FILTERED


class HeaderFilter:
    def __init__(self, headers=None, req_type=RequestType.ALL):
        self._headers = headers or []
        self._req_type = req_type

    def filter(self, log_record):
        if not isinstance(log_record, RequestLogRecord):
            return

        if self._req_type == RequestType.REQUEST or self._req_type == RequestType.ALL:
            filter_headers(self._headers, log_record._req_headers)

        if self._req_type == RequestType.RESPONSE or self._req_type == RequestType.ALL:
            filter_headers(self._headers, log_record._res_headers)


LOGGABLE_TYPES = ["application/json", "text/plain", "text/html"]
BODY_NOT_LOGGABLE = "<body not loggable Content-Type {}>"
JSON_BODY_FILTERED = "<filtered>"


def filter_body(body, content_type, allowed_types):
    if content_type and any(valid_type in content_type for valid_type in allowed_types):
        return body

    return BODY_NOT_LOGGABLE.format(content_type)


def find_content_type(headers):
    return ",".join(headers.getall("Content-Type"))


def filter_json_body(s, r):
    for k, v in s.items():
        if k in r:
            if isinstance(v, dict):
                filter_json_body(v, r[k])
            else:
                r[k] = JSON_BODY_FILTERED


class BodyTypeFilter:
    def __init__(self, allowed_types=None, req_type=RequestType.ALL):
        self._allowed_types = LOGGABLE_TYPES if allowed_types is None else allowed_types
        self._req_type = req_type

    def filter(self, log_record):
        if not isinstance(log_record, RequestLogRecord):
            return

        if log_record._req_body and (
            self._req_type == RequestType.REQUEST or self._req_type == RequestType.ALL
        ):
            content_type = find_content_type(log_record._req_headers)
            log_record._req_body = filter_body(
                log_record._req_body, content_type, self._allowed_types
            )

        if log_record._res_body and (
            self._req_type == RequestType.RESPONSE or self._req_type == RequestType.ALL
        ):
            content_type = find_content_type(log_record._res_headers)
            log_record._res_body = filter_body(
                log_record._res_body, content_type, self._allowed_types
            )


class JsonBodyFilter:
    def __init__(self, body_schema, req_type=RequestType.ALL):
        self._body_schema = body_schema or {}
        self._req_type = req_type

    def filter(self, log_record):
        if not isinstance(log_record, RequestLogRecord):
            return

        if log_record._req_body and (
            self._req_type == RequestType.REQUEST or self._req_type == RequestType.ALL
        ):
            if "application/json" in find_content_type(log_record._req_headers):
                req_body = rapidjson.loads(log_record._req_body)
                filter_json_body(self._body_schema, req_body)
                log_record._req_body = rapidjson.dumps(req_body)

        if log_record._res_body and (
            self._req_type == RequestType.RESPONSE or self._req_type == RequestType.ALL
        ):
            if "application/json" in find_content_type(log_record._res_headers):
                res_body = rapidjson.loads(log_record._res_body)
                filter_json_body(self._body_schema, res_body)
                log_record._res_body = rapidjson.dumps(res_body)
