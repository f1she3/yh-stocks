import logging
import sys

from pythonjsonlogger.json import JsonFormatter


class _ColorFormatter(logging.Formatter):
    _grey = "\x1b[38;21m"
    _green = "\x1b[32m"
    _yellow = "\x1b[33m"
    _red = "\x1b[31m"
    _bold_red = "\x1b[31;1m"
    _reset = "\x1b[0m"
    _fmt = "%(asctime)s - %(name)s(%(filename)s:%(lineno)d) - %(levelname)s - %(message)s"

    _FORMATS = {
        logging.DEBUG: _grey + _fmt + _reset,
        logging.INFO: _green + _fmt + _reset,
        logging.WARNING: _yellow + _fmt + _reset,
        logging.ERROR: _red + _fmt + _reset,
        logging.CRITICAL: _bold_red + _fmt + _reset,
    }

    def format(self, record: logging.LogRecord) -> str:
        formatter = logging.Formatter(self._FORMATS.get(record.levelno, self._fmt))
        return formatter.format(record)


def get_logger(name: str = "yh-stocks", level: str = "INFO") -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(level.upper())
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())
    if sys.stdout.isatty():
        handler.setFormatter(_ColorFormatter())
    else:
        handler.setFormatter(JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    return log


logger = get_logger()
