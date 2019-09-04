import logging
import pytest

from nephthys import BaseLoggerAdapter, Log, LogRecord


@pytest.fixture
def logger():
    return logging.getLogger("test_logger")


def log_generator(message=None, extra_tags=None):
    return Log(LogRecord(message=message, extra_tags=extra_tags))


@pytest.mark.parametrize(
    "tags,message,output",
    [
        ([], "test", {"extra_tags": ["test_logger"], "message": "test"}),
        (
            ["tag1", "tag2"],
            "",
            {"extra_tags": ["tag1", "tag2", "test_logger"], "message": ""},
        ),
        (
            ["tag1", "tag2"],
            "test",
            {"extra_tags": ["tag1", "tag2", "test_logger"], "message": "test"},
        ),
        (
            ["tag1", "tag2"],
            log_generator(message="test", extra_tags=["log_rec_tag"]),
            {
                "extra_tags": ["log_rec_tag", "tag1", "tag2", "test_logger"],
                "message": "test",
            },
        ),
    ],
)
def test_process(logger, tags, message, output):
    base_logger = BaseLoggerAdapter(logger, tags)
    log_dict, kwargs = base_logger.process(message, {})

    assert log_dict == output
