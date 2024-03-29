"""
This is a customized logger for the database project.
"""
import logging
from colorlog import ColoredFormatter
import os
import sys

# TODO: inlcude comments

# Setting color logs
SUCCESS = 21
FAIL = 22
PIPE = 55
LOG_LEVEL = logging.INFO
LOG_LEVEL_E = logging.ERROR
LOGFORMAT = '%(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s'
LOGFORMAT_ERROR = '%(log_color)s%(asctime)-8s%(reset)s | %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s'

# Adding file path for error logs and levels above
if sys.version_info[0] >= 3.8:
    FILE_PATH = os.path.join('docs/proj_logging/level_errors_logs.log')
else:
    FILE_PATH = os.path.join(os.getcwd(), 'docs/proj_logging/level_errors_logs.log')

logging.addLevelName(SUCCESS, "SUCCESS")


def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS):
        self._log(SUCCESS, message, args, **kws)


logging.addLevelName(FAIL, "FAIL")


def fail(self, message, *args, **kws):
    if self.isEnabledFor(FAIL):
        self._log(FAIL, message, args, **kws)


logging.addLevelName(PIPE, "PIPE")


def pipe(self, message, *args, **kws):
    if self.isEnabledFor(PIPE):
        self._log(PIPE, message, args, **kws)


logging.Logger.success = success
logging.Logger.fail = fail
logging.Logger.pipe = pipe
logging.root.setLevel(LOG_LEVEL)

formatter = ColoredFormatter(
            LOGFORMAT,
            log_colors={
                        'DEBUG': 'white,bg_black',
                        'INFO': 'cyan',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_black',
                        'SUCCESS': 'bold_green',
                        'FAIL': 'white,bg_black',
                        'PIPE': 'green'
                    })
e_formatter = ColoredFormatter(
            LOGFORMAT_ERROR,
            log_colors={
                        'DEBUG': 'white,bg_black',
                        'INFO': 'cyan',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'bold_red,bg_black',
                        'SUCCESs': 'bold_green',
                        'FAIL': 'white, bg_black',
                        'PIPE': 'green'
                        })

stream = logging.StreamHandler()
file_handler = logging.FileHandler(FILE_PATH)

stream.setLevel(LOG_LEVEL)
# TODO: Only save loglevel error to file
file_handler.setLevel(LOG_LEVEL_E)

stream.setFormatter(formatter)
file_handler.setFormatter(e_formatter)

log = logging.getLogger('pythonConfig')
log.setLevel(LOG_LEVEL)
if (log.hasHandlers()):
    log.handlers.clear()
log.addHandler(stream)
log.addHandler(file_handler)
