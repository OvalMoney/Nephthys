import logging
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from requests.sessions import Session as RequestsSession

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
            if isinstance(request.body, str):
                log_record.request_body = request.body
            else:
                log_record.request_body = request.body.decode("UTF-8", errors="strict")
        except UnicodeDecodeError:
            log_record.request_body = "<RAW Data>"


def decorate_log_response(log_record, response):
    log_record.status_code = response.status_code

    if response.headers:
        for name, value in response.headers.items():
            log_record.add_response_header(name, value)

    if response.content:
        encoding = response.encoding or "utf-8"

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

    def __init__(self, log_tag=None, log_filters=None, *args, **kwargs):
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
        super().__init__(*args, **kwargs)

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


class Session(NephthysMixin, RequestsSession):
    """
    Provides a requests.session.Session with Nephthys Logging.
    """
    pass
