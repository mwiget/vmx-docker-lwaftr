__author__ = "Amish Anand"
__copyright__ = "Copyright (c) 2016 Juniper Networks, Inc."

import logging
from logging.handlers import RotatingFileHandler

# Logging Parameters
DEFAULT_LOG_FILE_NAME = '/tmp/jetapp.log'
DEFAULT_LOG_LEVEL = logging.INFO

# Enable Logging to a file
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s ] %(message)s"
logging.basicConfig(filename=DEFAULT_LOG_FILE_NAME, level=DEFAULT_LOG_LEVEL, format = FORMAT)
rotation_handler = logging.handlers.RotatingFileHandler(
              DEFAULT_LOG_FILENAME, maxBytes=1024*1024, backupCount=5)
LOG = logging.getLogger(__name__)
LOG.addHandler(rotation_handler)

