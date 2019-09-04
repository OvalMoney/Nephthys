import logging
import rapidjson
import re


class JSONRenderer:
    def __init__(self, sort_keys=False, indent=None):
        self._sort_keys = sort_keys
        self._indent = indent

    def __call__(self, content):
        return rapidjson.dumps(
            content,
            default=self.default,
            sort_keys=self._sort_keys,
            indent=self._indent,
        )

    def default(self, content):
        return str(content)


class JSONFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.render_exc = kwargs.pop("render_exc", True)

        sort_keys = kwargs.pop("json_sort_keys", False)
        indent = kwargs.pop("json_indent", None)

        super().__init__(*args, **kwargs)

        self._renderer = JSONRenderer(indent=indent, sort_keys=sort_keys)
        self._required_fields = self._parse()

    def _parse(self):
        """
        Parses format string looking for substitutions
        This method is responsible for returning a list of fields (as strings)
        to include in all log messages.
        """
        standard_formatters = re.compile(r"\((.+?)\)", re.IGNORECASE)
        return standard_formatters.findall(self._fmt)

    def _add_fields(self, log_record, record, message_dict):
        """
        Override this method to implement custom logic for adding fields.
        """
        for field in self._required_fields:
            log_record[field] = record.__dict__.get(field)
        log_record.update(message_dict)

    def format(self, record):
        """Formats a log record and serializes to json"""
        message_dict = {}
        if isinstance(record.msg, dict):
            message_dict = record.msg
        else:
            record.message = record.getMessage()

        if self.render_exc:
            # Display formatted exception, but allow overriding it in the
            # user-supplied dict.
            if record.exc_info and not message_dict.get("exc_info"):
                message_dict["exc_info"] = self.formatException(record.exc_info)
            if not message_dict.get("exc_info") and record.exc_text:
                message_dict["exc_info"] = record.exc_text
            # Display formatted record of stack frames
            # default format is a string returned from :func:`traceback.print_stack`
            if record.stack_info and not message_dict.get("stack_info"):
                message_dict["stack_info"] = self.formatStack(record.stack_info)

        log_record = {}

        self._add_fields(log_record, record, message_dict)

        return self._renderer(log_record)
