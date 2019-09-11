import logging
import pytest

from nephthys.filters.message import MessageBlacklist
from nephthys import FilterLoggerAdapter, FilterableLog, Log, LogRecord


@pytest.fixture
def logger():
    return logging.getLogger("test_logger")


def log_generator(message=None, extra_tags=None):
    return Log(LogRecord(message=message, extra_tags=extra_tags))


def filt_log_generator(record_filter=None, message=None, extra_tags=None):
    filt_log = FilterableLog(LogRecord(message=message, extra_tags=extra_tags))
    if record_filter:
        filt_log.add_filters([record_filter])
    return filt_log


@pytest.mark.parametrize(
    "filters,message,output",
    [
        ([], "test", {"extra_tags": ["test_logger"], "message": "test"}),
        ([], "", {"extra_tags": ["test_logger"], "message": ""}),
        ([], "test", {"extra_tags": ["test_logger"], "message": "test"}),
        (
            [MessageBlacklist(["blacklisted"])],
            "blacklisted test blacklisted",
            {"extra_tags": ["test_logger"], "message": "<filtered> test <filtered>"},
        ),
        (
            [],
            log_generator(message="test", extra_tags=["log_rec_tag"]),
            {"extra_tags": ["log_rec_tag", "test_logger"], "message": "test"},
        ),
        (
            [MessageBlacklist(["blacklisted"])],
            log_generator(message="blacklisted test blacklisted"),
            {"extra_tags": ["test_logger"], "message": "<filtered> test <filtered>"},
        ),
        (
            [MessageBlacklist(["blacklisted_1"])],
            filt_log_generator(
                record_filter=MessageBlacklist(["blacklisted_2"]),
                message="blacklisted_1 test blacklisted_2",
            ),
            {"extra_tags": ["test_logger"], "message": "<filtered> test <filtered>"},
        ),
    ],
)
def test_process(logger, filters, message, output):
    base_logger = FilterLoggerAdapter(logger, filters=filters)
    log_dict, kwargs = base_logger.process(message, {})

    assert log_dict == output
