import re

from .filter import IFilter
from .. import LogRecord

FILTER_STRING = "<filtered>"


class MessageBlacklist(IFilter):
    def __init__(self, blacklist=None):
        self._blacklist = blacklist or []
        self._blacklist_string = "|".join(self._blacklist)

    def filter(self, log_record):
        if not isinstance(log_record, LogRecord):
            return

        log_record._message = re.sub(
            self._blacklist_string, FILTER_STRING, log_record._message
        )
