from abc import ABC, abstractmethod


class IFilter(ABC):
    @abstractmethod
    def filter(self, log_record):
        """
        Applies configured filters to log_record
        :param log_record: The record that needs to be filtered
        :type log_record: LogRecord
        """
        pass  # pragma: nocover
