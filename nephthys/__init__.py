import itertools
from logging import LoggerAdapter
from webob.multidict import MultiDict
from urllib.parse import urlparse


class BaseLoggerAdapter(LoggerAdapter):
    def __init__(self, logger, extra_tags=None, *args, **kwargs):
        super().__init__(logger=logger, extra=None, *args, **kwargs)

        self._extra_tags = extra_tags or []
        self._extra_tags.append(logger.name)

    def _process(self, msg):
        if isinstance(msg, str):
            msg = Log(LogRecord(message=msg))

        if isinstance(msg, Log):
            log_rec = msg.log_record
            log_rec.add_tags(self._extra_tags)

        return msg

    def process(self, msg, kwargs):

        proc_msg = self._process(msg)

        if isinstance(proc_msg, Log):
            return proc_msg.log_record.asdict(), kwargs

        return proc_msg, kwargs


def apply_filters(log_record, filters):
    for f in filters:
        if hasattr(f, "filter"):
            f.filter(log_record)
        else:
            f(log_record)


class FilterLoggerAdapter(BaseLoggerAdapter):
    def __init__(self, logger, filters=None, *args, **kwargs):
        super().__init__(logger=logger, *args, **kwargs)

        self._filters = filters or []

    def _process(self, msg):
        msg = super()._process(msg)

        if isinstance(msg, Log):
            log_rec = msg.log_record
            filters = self._filters

            if isinstance(msg, FilterableLog):
                filters = itertools.chain(filters, msg.filters)

            apply_filters(log_rec, filters)

        return msg

    def log(self, level, msg, *args, **kwargs):
        if isinstance(msg, FilterableLog) and msg.drop:
            return

        super().log(level, msg, *args, **kwargs)


def join_multidict(multi_dict):
    list_dict = multi_dict.dict_of_lists()
    return {key: ",".join(value) for key, value in list_dict.items()}


def add_to_multidict(multi_dict, name, value):
    if isinstance(value, list):
        for val in value:
            multi_dict.add(name, str(val))
    else:
        multi_dict.add(name, str(value))


class Log:
    def __init__(self, log_record):
        self._log_record = log_record

    @property
    def log_record(self):
        return self._log_record


class FilterableLog(Log):
    def __init__(self, log_record):
        super().__init__(log_record)
        self.drop = False
        self._filters = []

    @property
    def filters(self):
        return self._filters

    def add_filters(self, record_filters):
        if isinstance(record_filters, list):
            self._filters.extend(record_filters)
        else:
            self._filters.append(record_filters)


class LogRecord:
    def __init__(self, message="", extra_tags=None, *args, **kwargs):
        self._extra_tags = extra_tags or []
        self._message = message

    def asdict(self):
        msg_dict = {"extra_tags": self._extra_tags, "message": self._message}

        return msg_dict

    def add_tags(self, tags):
        if isinstance(tags, list):
            self._extra_tags.extend(tags)
        else:
            self._extra_tags.append(tags)


class RequestLogRecord(LogRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._req_start = None
        self._req_end = None
        self._req_time = None
        self._method = None
        self._url = None
        self._path = None
        self._host = None
        self._route = None
        self._status_code = None
        self._user = None
        self._user_uuid = None
        self._req_query = MultiDict()
        self._req_headers = MultiDict()
        self._req_body = None
        self._res_headers = MultiDict()
        self._res_body = None
        self._route_match = {}

    def asdict(self):
        base_dict = super().asdict()

        req_dict = {
            "request": {
                "start": self._req_start,
                "end": self._req_end,
                "time": self._req_time,
                "method": self._method,
                "header": join_multidict(self._req_headers),
                "query": join_multidict(self._req_query),
                "url": self._url,
                "host": self._host,
                "path": self._path,
                "route": self._route,
                "route_match": self._route_match,
                "user": self._user,
                "user_uuid": self._user_uuid,
                "body": self._req_body,
            },
            "response": {
                "status_code": self._status_code,
                "header": join_multidict(self._res_headers),
                "body": self._res_body,
            },
        }

        return {**base_dict, **req_dict}

    def add_request_querystring(self, name, value):
        add_to_multidict(self._req_query, name, value)

    def add_request_header(self, name, value):
        name = name.title()
        add_to_multidict(self._req_headers, name, value)

    def add_response_header(self, name, value):
        name = name.title()
        add_to_multidict(self._res_headers, name, value)

    def add_route_match(self, name, value):
        self._route_match[name] = value

    def _set_request_start(self, value):
        self._req_start = value

        if self._req_end:
            self._req_time = (self._req_end - self._req_start) * 1000

    def _set_request_end(self, value):
        self._req_end = value

        if self._req_start:
            self._req_time = (self._req_end - self._req_start) * 1000

    def _set_request_body(self, body):
        self._req_body = body

    def _set_response_body(self, body):
        self._res_body = body

    def _set_method(self, value):
        self._method = value.upper()

    def _set_url(self, value):
        parsed_url = urlparse(value)

        self._url = value
        self._path = parsed_url.path
        self._host = parsed_url.netloc

    def _set_route(self, value):
        self._route = value

    def _set_status_code(self, value):
        _val = int(value)
        if _val > 599 or _val < 100:
            raise ValueError

        self._status_code = int(value)

    def _set_user(self, value):
        self._user = value

    def _set_user_uuid(self, value):
        self._user_uuid = value

    request_start = property(None, _set_request_start)
    request_end = property(None, _set_request_end)
    request_body = property(None, _set_request_body)
    response_body = property(None, _set_response_body)
    method = property(None, _set_method)
    url = property(None, _set_url)
    route = property(None, _set_route)
    status_code = property(None, _set_status_code)
    user = property(None, _set_user)
    user_uuid = property(None, _set_user_uuid)
