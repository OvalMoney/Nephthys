import logging
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from requests.sessions import Session

from nephthys import FilterLoggerAdapter, RequestLogRecord, Log
from nephthys.filters.requests import BodyTypeFilter

logger = logging.getLogger("requests_out")

DEFAULT_ALLOWED_TYPES = [
    "application/json",
    "text/plain",
    "text/html",
    "application/x-www-form-urlencoded",
]


def catch_logger_exception(function):
    def wrapper(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except Exception as exc:
            logger.exception("Failed to log")

    return wrapper


def decorate_log_request(log_record, request):
    log_record.method = request.method
    log_record.url = request.url

    if request.headers:
        for name, value in request.headers.items():
            log_record.add_request_header(name, value)

    querystring = parse_qs(urlparse(request.url).query)
    if querystring:
        for name, value in querystring.items():
            log_record.add_request_querystring(name, value)
    if request.body:
        try:
            log_record.request_body = request.body.decode("UTF-8", errors="strict")
        except UnicodeDecodeError:
            log_record.request_body = "<RAW Data>"


def decorate_log_response(log_record, response):
    log_record.status_code = response.status_code

    if response.headers:
        for name, value in response.headers.items():
            log_record.add_response_header(name, value)

    if response.content:
        encoding = response.encoding
        if encoding is None:
            encoding = "utf-8"
        # Forcefully remove BOM from UTF-8
        elif encoding.lower() == "utf-8":
            encoding = "utf-8-sig"

        try:
            log_record.response_body = response.content.decode(
                encoding, errors="strict"
            )
        except (TypeError, LookupError, UnicodeDecodeError):
            log_record.response_body = "<RAW Data>"


class NephthysMixin:
    """
    Provides an easy way to add a nephthys logger a class.
    The logger is configured with a default nephthys.filters.requests.BodyTypeFilter,
    instantiated with nephthys.clients.requests_session.DEFAULT_ALLOWED_TYPES as its
    allowed_types.
    """

    _logger = None

    def init_nephthys_logger(self, log_tag, log_filters):
        """
        :param log_tag: The tag that will identify logs from this Session
        :type log_tag: string
        :param log_filters: List of additional IRequestFilter
        :type log_filters: list
        """
        _log_filters = [BodyTypeFilter(allowed_types=DEFAULT_ALLOWED_TYPES)]

        if isinstance(log_filters, list):
            _log_filters.extend(log_filters)

        self._logger = FilterLoggerAdapter(
            logger=logger, filters=_log_filters, extra_tags=[log_tag]
        )

    @catch_logger_exception
    def _send_log_record(
        self, start_time, end_time, request=None, response=None, exception=False
    ):
        """
        Builds a LogRecord and logs it with self._logger.
        Integrate this method in your class to enable Nephthys logging into it.
        :param start_time: timestamp of when the operation logged started
        :param end_time: timestamp of when the operation logged ended
        :type request: requests.models.Request
        :type response: requests.models.Response
        :param exception: whether the log is an exception or not
        """
        log_rec = RequestLogRecord()
        log_rec.request_start = start_time
        log_rec.request_end = end_time

        decorate_log_request(log_rec, request)

        if response is not None:
            decorate_log_response(log_rec, response)

        if exception:
            self._logger.exception(Log(log_rec))
        else:
            self._logger.info(Log(log_rec))


class NephthysSession(Session, NephthysMixin):
    """
    Provides a requests.session.Session overriding .send() method so that it logs
    each request with an instance of nephthys.FilterLoggerAdapter.

    This class can be used as a concrete implementation of requests.session.Session
    in an existing project.
    If said project already uses a custom implementation of Session, this class can
    be used as an example of how to add NephthysMixin to it.
    """

    def __init__(self, log_tag=None, log_filters=None):
        """
        :param log_tag: The tag that will identify logs from this Session
        :type log_tag: string
        :param log_filters: List of additional IRequestFilter
        :type log_filters: list
        """
        super().__init__()
        self.init_nephthys_logger(log_tag, log_filters)

    def send(self, request, **kwargs):
        start_time = datetime.utcnow().timestamp()

        try:
            response = super().send(request, **kwargs)
        except Exception as exc:
            self._send_log_record(
                start_time=start_time,
                end_time=datetime.utcnow().timestamp(),
                request=request,
                exception=True,
            )
            raise

        self._send_log_record(
            start_time=start_time,
            end_time=datetime.utcnow().timestamp(),
            request=request,
            response=response,
        )

        return response
