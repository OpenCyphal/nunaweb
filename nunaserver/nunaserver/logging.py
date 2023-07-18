import logging
import os, sys, time
from nunaserver import settings

log_file = None


def init_logging():
    # Setup logging
    global log_file

    if log_file:
        return

    if settings.LOG_FILE == "stderr":
        log_file = sys.stderr
    else:
        log_file = settings.LOG_FILE

    log_handler = logging.FileHandler(log_file)
    loggers = [logging.getLogger()]
    loggers = loggers + [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logger in loggers:
        logger.setLevel(settings.LOG_LEVEL)
        logger.addHandler(log_handler)
