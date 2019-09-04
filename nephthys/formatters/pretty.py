import logging
import copy
from .json import JSONRenderer


class PrettyFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        sort_keys = kwargs.pop("json_sort_keys", True)
        indent = kwargs.pop("json_indent", 2)
        self._renderer = JSONRenderer(indent=indent, sort_keys=sort_keys)

        super().__init__(*args, **kwargs)

    def format(self, record):

        if isinstance(record.msg, dict):
            record.message = self._renderer(copy.deepcopy(record.msg))
        else:
            record.message = record.getMessage()

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        s = self.formatMessage(record)
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)
        return s
