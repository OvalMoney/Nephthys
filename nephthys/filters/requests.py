import rapidjson
from enum import Enum

from .filter import IFilter
from .. import RequestLogRecord


QS_FILTERED = "<filtered>"
HEADER_FILTERED = "<filtered>"
LOGGABLE_TYPES = ["application/json", "text/plain", "text/html"]
BODY_NOT_LOGGABLE = "<body not loggable Content-Type {}>"
JSON_BODY_FILTERED = "<filtered>"


def filter_json_body(s, r):
    for k, v in s.items():
        if k in r:
            if isinstance(v, dict):
                filter_json_body(v, r[k])
            else:
                r[k] = JSON_BODY_FILTERED


def find_content_type(headers):
    return ",".join(headers.getall("Content-Type"))


class RequestType(Enum):
    ALL = 1
    REQUEST = 2
    RESPONSE = 3


class HeaderFilter(IFilter):
    def __init__(self, headers=None, req_type=RequestType.ALL):
        self._headers = headers or []
        self._req_type = req_type

    def _filter_headers(self, headers):
        for hf in self._headers:
            hft = hf.title()
            if hft in headers:
                headers[hft] = HEADER_FILTERED

    def filter(self, log_record):
        if not isinstance(log_record, RequestLogRecord):
            return

        if self._req_type == RequestType.REQUEST or self._req_type == RequestType.ALL:
            self._filter_headers(log_record._req_headers)

        if self._req_type == RequestType.RESPONSE or self._req_type == RequestType.ALL:
            self._filter_headers(log_record._res_headers)


class QueryStringFilter(IFilter):
    def __init__(self, keys=None):
        self._keys = keys or []

    def _filter_keys(self, keys):
        for kf in self._keys:
            if kf in keys:
                keys[kf] = QS_FILTERED

    def filter(self, log_record):
        if not isinstance(log_record, RequestLogRecord):
            return

        self._filter_keys(log_record._req_query)


class BodyTypeFilter(IFilter):
    def __init__(self, allowed_types=None, req_type=RequestType.ALL):
        self._allowed_types = LOGGABLE_TYPES if allowed_types is None else allowed_types
        self._req_type = req_type

    def _filter_body(self, body, content_type):
        if content_type and any(valid_type in content_type for valid_type in self._allowed_types):
            return body

        return BODY_NOT_LOGGABLE.format(content_type)

    def filter(self, log_record):
        if not isinstance(log_record, RequestLogRecord):
            return

        if log_record._req_body and (
            self._req_type == RequestType.REQUEST or self._req_type == RequestType.ALL
        ):
            content_type = find_content_type(log_record._req_headers)
            log_record._req_body = self._filter_body(
                log_record._req_body, content_type
            )

        if log_record._res_body and (
            self._req_type == RequestType.RESPONSE or self._req_type == RequestType.ALL
        ):
            content_type = find_content_type(log_record._res_headers)
            log_record._res_body = self._filter_body(
                log_record._res_body, content_type
            )


class JsonBodyFilter(IFilter):
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
